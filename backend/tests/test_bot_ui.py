import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import EditMessageText
from aiogram.types import Message
from apps.accounts.models import StudentProfile
from apps.attempts.models import Attempt
from apps.quizzes.models import Quiz
from django.utils import timezone

from bot.handlers.main import callback
from bot.keyboards.exam import menu
from bot.ui import Panel, text_chunks, text_entities

pytestmark = pytest.mark.django_db(transaction=True)


def message(text="Previous screen", markup=None):
    result = MagicMock(spec=Message)
    result.chat = SimpleNamespace(id=8131)
    result.message_id = 15
    result.text = text
    result.photo = None
    result.reply_markup = markup
    result.answer = AsyncMock()
    result.edit_text = AsyncMock()
    result.edit_media = AsyncMock()
    result.edit_caption = AsyncMock()
    result.edit_reply_markup = AsyncMock()
    return result


def event(panel, data):
    return SimpleNamespace(
        message=panel, from_user=SimpleNamespace(id=8131), data=data, answer=AsyncMock()
    )


def test_menu_gives_test_selection_priority_and_keeps_all_six_features():
    rows = menu().inline_keyboard
    assert [len(row) for row in rows] == [1, 2, 2, 1]
    assert {b.callback_data for row in rows for b in row} == {
        "list:0",
        "code",
        "resume",
        "results",
        "ranking",
        "profile",
    }


def test_same_panel_avoids_redundant_network_request():
    panel = message("Existing", menu())
    asyncio.run(Panel(panel).answer("Existing", reply_markup=menu()))
    panel.edit_text.assert_not_awaited()
    panel.answer.assert_not_awaited()


def test_deleted_panel_falls_back_once_without_deleting_chat_history():
    panel = message()
    panel.edit_text.side_effect = TelegramBadRequest(
        method=EditMessageText(chat_id=8131, message_id=15, text="Next"),
        message="Bad Request: message to edit not found",
    )
    asyncio.run(Panel(panel).answer("Next", reply_markup=menu()))
    panel.edit_text.assert_awaited_once()
    panel.answer.assert_awaited_once()


def test_other_edit_errors_do_not_create_duplicate_messages():
    panel = message()
    panel.edit_text.side_effect = TelegramBadRequest(
        method=EditMessageText(chat_id=8131, message_id=15, text="Next"),
        message="Bad Request: invalid callback data",
    )
    with pytest.raises(TelegramBadRequest):
        asyncio.run(Panel(panel).answer("Next"))
    panel.answer.assert_not_awaited()


def test_emoji_chunks_and_heading_offsets_respect_telegram_utf16():
    text = "📝 Quiz\n" + "🙂" * 5000 + " end"
    chunks = list(text_chunks(text))
    assert "".join(chunks) == text
    assert all(len(chunk.encode("utf-16-le")) // 2 <= 3800 for chunk in chunks)
    assert text_entities(text)[0].length == 7


def test_public_pagination_edits_one_panel_and_caps_controls(teacher):
    StudentProfile.objects.create(telegram_id=8131, full_name="Panel Student")
    for i in range(12):
        Quiz.objects.create(
            owner=teacher, title=f"Quiz {i:02}", subject="Fan", status="published"
        )
    panel = message()
    state = SimpleNamespace(clear=AsyncMock(), set_state=AsyncMock())
    c = event(panel, "list:0")
    asyncio.run(callback(c, state))
    panel.edit_text.assert_awaited_once()
    panel.answer.assert_not_awaited()
    first = panel.edit_text.call_args
    assert "Quiz 00" in first.args[0] and "Quiz 04" not in first.args[0]
    rows = first.kwargs["reply_markup"].inline_keyboard
    assert [row[0].text for row in rows[:4]] == [
        f"{i + 1}. Quiz {i:02}" for i in range(4)
    ]
    assert rows[0][0].callback_data.startswith("q:")
    assert rows[0][0].callback_data.endswith(":0")
    assert "10 savol · 30 daqiqa" in first.args[0]
    assert "1/1 qoldi · Qatnashish mumkin" in first.args[0]
    assert len(rows) <= 6
    c.data = "list:1"
    asyncio.run(callback(c, state))
    second = panel.edit_text.call_args
    assert "Quiz 04" in second.args[0] and "Quiz 00" not in second.args[0]
    assert panel.edit_text.await_count == 2
    panel.answer.assert_not_awaited()


def test_callback_acknowledgement_does_not_delay_rendering():
    StudentProfile.objects.create(telegram_id=8131, full_name="Fast Student")
    panel = message()

    async def journey():
        acknowledgement_started = asyncio.Event()
        render_started = asyncio.Event()

        async def acknowledge():
            acknowledgement_started.set()
            await asyncio.wait_for(render_started.wait(), timeout=2)

        async def render(*args, **kwargs):
            await asyncio.wait_for(acknowledgement_started.wait(), timeout=2)
            render_started.set()

        panel.edit_text.side_effect = render
        c = event(panel, "menu")
        c.answer.side_effect = acknowledge
        await asyncio.wait_for(
            callback(c, SimpleNamespace(clear=AsyncMock(), set_state=AsyncMock())),
            timeout=5,
        )

    asyncio.run(journey())
    panel.edit_text.assert_awaited_once()
    panel.answer.assert_not_awaited()


def test_result_history_is_one_paginated_panel_instead_of_a_message_burst(teacher):
    student = StudentProfile.objects.create(
        telegram_id=8131, full_name="Result Student"
    )
    quiz = Quiz.objects.create(
        owner=teacher, title="History", subject="Fan", show_ranking=False
    )
    now = timezone.now()
    for i in range(12):
        Attempt.objects.create(
            quiz=quiz,
            student=student,
            number=i + 1,
            status="completed",
            navigation="free",
            started_at=now,
            deadline=now,
            finished_at=now,
            percentage=i,
        )
    panel = message()
    asyncio.run(
        callback(event(panel, "results"), SimpleNamespace(set_state=AsyncMock()))
    )
    panel.edit_text.assert_awaited_once()
    panel.answer.assert_not_awaited()
    text = panel.edit_text.call_args.args[0]
    assert "1/12" in text and "History" in text
    buttons = panel.edit_text.call_args.kwargs["reply_markup"].inline_keyboard
    assert any(b.callback_data == "results:1" for row in buttons for b in row)


def image_question(teacher):
    import io

    from apps.questions.models import Question
    from django.core.files.base import ContentFile
    from PIL import Image

    question = Question.objects.create(
        owner=teacher,
        text="Image cache",
        options=["a", "b", "c", "d"],
        correct_option=0,
    )
    image = io.BytesIO()
    Image.new("RGB", (8, 8)).save(image, format="PNG")
    question.image.save("cache.png", ContentFile(image.getvalue()))
    return question


def photo_response():
    from aiogram.types import Chat, PhotoSize

    return Message(
        message_id=15,
        date=timezone.now(),
        chat=Chat(id=8131, type="private"),
        photo=[
            PhotoSize(
                file_id="cached-image", file_unique_id="unique-image", width=8, height=8
            )
        ],
    )


def test_question_photo_reuses_file_id_and_edits_caption_without_upload(teacher):
    from unittest.mock import patch

    from bot import services
    from bot.handlers.presentation import question_photo

    question = image_question(teacher)
    panel = message()
    panel.bot = SimpleNamespace(id=9921)
    sent = photo_response()
    panel.edit_media.return_value = sent
    panel.edit_caption.return_value = sent
    with patch("bot.services.image_data", wraps=services.image_data) as read_image:
        assert asyncio.run(
            question_photo(Panel(panel), question.image.name, "First question", menu())
        )
        panel.photo = sent.photo
        assert asyncio.run(
            question_photo(Panel(panel), question.image.name, "Saved answer", menu())
        )
    assert read_image.call_count == 1
    panel.edit_media.assert_awaited_once()
    panel.edit_caption.assert_awaited_once()
    panel.answer.assert_not_awaited()


def test_rejected_cached_photo_id_is_evicted_and_real_image_reuploaded(teacher):
    from aiogram.methods import EditMessageMedia
    from aiogram.types import InputMediaPhoto

    from bot import services
    from bot.handlers.presentation import question_photo

    question = image_question(teacher)
    panel = message()
    panel.bot = SimpleNamespace(id=9922)
    services.remember_photo(9922, question.image.name, "stale-image")
    error = TelegramBadRequest(
        method=EditMessageMedia(
            chat_id=8131, message_id=15, media=InputMediaPhoto(media="stale-image")
        ),
        message="Bad Request: wrong file identifier",
    )
    panel.edit_media.side_effect = [error, photo_response()]
    assert asyncio.run(
        question_photo(Panel(panel), question.image.name, "Question", menu())
    )
    assert panel.edit_media.await_count == 2
    assert panel.edit_media.call_args.kwargs["media"].media.filename == "savol.png"
    assert services.photo_file_id(9922, question.image.name) == "cached-image"
    panel.answer.assert_not_awaited()


def test_rapid_repeated_taps_share_updated_panel_and_do_not_repeat_edit():
    from aiogram.types import Chat

    StudentProfile.objects.create(telegram_id=8131, full_name="Rapid Student")
    panel = message()
    panel.edit_text.return_value = Message(
        message_id=15,
        date=timezone.now(),
        chat=Chat(id=8131, type="private"),
        text="Salom, Rapid!\n\nYangi test uchun «Test tanlash»ni bosing.\nO‘qituvchingiz kod bergan bo‘lsa, «Kod bilan kirish»ni tanlang.",
        reply_markup=menu(),
    )

    async def taps():
        await asyncio.gather(
            callback(
                event(panel, "menu"),
                SimpleNamespace(clear=AsyncMock(), set_state=AsyncMock()),
            ),
            callback(
                event(panel, "menu"),
                SimpleNamespace(clear=AsyncMock(), set_state=AsyncMock()),
            ),
        )

    asyncio.run(taps())
    panel.edit_text.assert_awaited_once()
    panel.answer.assert_not_awaited()


def test_catalog_remaining_attempts_are_scoped_and_active_attempt_can_resume(teacher):
    from datetime import timedelta

    own = StudentProfile.objects.create(telegram_id=8131, full_name="Catalog Student")
    other = StudentProfile.objects.create(telegram_id=8132, full_name="Other Student")
    quiz = Quiz.objects.create(
        owner=teacher, title="Own limit", subject="Fan", status="published"
    )
    now = timezone.now()
    for person, status in [(own, "in_progress"), (other, "completed")]:
        Attempt.objects.create(
            quiz=quiz,
            student=person,
            number=1,
            status=status,
            navigation="free",
            started_at=now,
            deadline=now + timedelta(minutes=10),
        )
    panel = message()
    asyncio.run(
        callback(event(panel, "list:0"), SimpleNamespace(set_state=AsyncMock()))
    )
    text = panel.edit_text.call_args.args[0]
    assert "0/1 qoldi · Boshlangan · davom ettirish mumkin" in text
    Attempt.objects.filter(student=own).update(status="completed", finished_at=now)
    asyncio.run(
        callback(event(panel, "list:0"), SimpleNamespace(set_state=AsyncMock()))
    )
    assert "0/1 qoldi · Urinishlar tugagan" in panel.edit_text.call_args.args[0]


def test_new_result_layout_never_invents_hidden_fields_or_unreleased_answers():
    from bot.handlers.presentation import result_text

    text = result_text({"released": True, "title": "Hidden score", "unanswered": 2})
    assert "Hidden score" in text and "Javobsiz: 2" in text
    assert "Ball:" not in text and "%" not in text and "To‘g‘ri:" not in text
    hidden = result_text(
        {
            "released": False,
            "title": "PRIVATE",
            "percentage": 99,
            "questions": [{"text": "SECRET"}],
        },
        details=True,
    )
    assert all(value not in hidden for value in ["PRIVATE", "99", "SECRET"])
    full = result_text(
        {
            "released": True,
            "title": "Visible",
            "earned": 7,
            "maximum": 10,
            "percentage": 70,
            "correct": 7,
            "questions": [
                {"text": "2+2", "options": ["3", "4"], "correct": 1, "selected": 0}
            ],
        },
        details=True,
    )
    assert "70.00%" in full and "Ball: 7 / 10" in full
    assert "Sizning javobingiz: 3" in full and "To‘g‘ri javob: 4" in full


def test_code_flow_updates_own_prompt_and_exits_input_state_on_success(teacher):
    from unittest.mock import patch

    from aiogram import Bot
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.storage.base import StorageKey
    from aiogram.fsm.storage.memory import MemoryStorage
    from aiogram.methods import EditMessageText
    from aiogram.types import Chat, User
    from apps.questions.models import Question, QuizQuestion
    from apps.quizzes.services import transition

    from bot.handlers.registration import Registration, code, continue_exam

    StudentProfile.objects.create(telegram_id=9924, full_name="Code Student")
    quiz = Quiz.objects.create(
        owner=teacher,
        title="Private exam",
        subject="Fan",
        access="private",
        question_count=1,
    )
    question = Question.objects.create(
        owner=teacher, text="2+2?", options=["1", "2", "3", "4"], correct_option=3
    )
    QuizQuestion.objects.create(quiz=quiz, question=question, position=0)
    transition(quiz, "published")
    quiz.refresh_from_db()
    access_code = quiz.access_code.code

    async def journey():
        bot = Bot("123456:test-only")
        storage = MemoryStorage()
        state = FSMContext(
            storage, StorageKey(bot_id=bot.id, chat_id=9924, user_id=9924)
        )
        await state.set_state(Registration.code)
        await state.update_data(code_prompt_id=40, code_prompt_chat=9924)
        chat = Chat(id=9924, type="private")
        returned = Message(message_id=40, date=timezone.now(), chat=chat)
        base = {
            "message_id": 41,
            "date": timezone.now(),
            "chat": chat,
            "from_user": User(id=9924, is_bot=False, first_name="Code"),
        }
        with patch.object(
            bot.session, "make_request", new=AsyncMock(return_value=returned)
        ) as transport:
            await code(Message(**base, text="WRONG").as_(bot), state)
            assert await state.get_state() == Registration.code.state
            first = transport.call_args.args[1]
            assert isinstance(first, EditMessageText) and first.message_id == 40
            assert "Kod topilmadi" in first.text
            # Choosing a different screen must leave code entry without
            # consuming the next ordinary message as another access code.
            await callback(
                SimpleNamespace(
                    message=returned.as_(bot),
                    from_user=base["from_user"],
                    data="results",
                    answer=AsyncMock(),
                ),
                state,
            )
            assert await state.get_state() is None
            await state.set_state(Registration.code)
            await code(Message(**base, text=access_code.lower()).as_(bot), state)
            assert await state.get_state() is None
            assert (await state.get_data())["code"] == access_code
            last = transport.call_args.args[1]
            assert last.message_id == 40 and last.chat_id == 9924
            assert "Private exam" in last.text
            callbacks = {
                b.callback_data
                for row in last.reply_markup.inline_keyboard
                for b in row
            }
            assert f"s:{quiz.pk}" in callbacks
            assert not any(value.startswith("list:") for value in callbacks)
            assert all(
                isinstance(call.args[1], EditMessageText)
                and call.args[1].message_id != 41
                for call in transport.call_args_list
            )
            await state.set_state(Registration.code)
            await continue_exam(Message(**base, text="/continue").as_(bot), state)
            assert await state.get_state() is None
            assert (await state.get_data())["code"] == access_code
        await storage.close()
        await bot.session.close()

    asyncio.run(journey())


def test_code_prompt_cannot_target_another_chat():
    from unittest.mock import patch

    from aiogram import Bot
    from aiogram.methods import SendMessage
    from aiogram.types import Chat, User

    from bot.handlers.registration import code

    async def journey():
        bot = Bot("123456:test-only")
        incoming = Message(
            message_id=71,
            date=timezone.now(),
            chat=Chat(id=9925, type="private"),
            from_user=User(id=9925, is_bot=False, first_name="Code"),
            text="bad",
        ).as_(bot)
        state = SimpleNamespace(
            get_data=AsyncMock(
                return_value={"code_prompt_id": 40, "code_prompt_chat": 9999}
            )
        )
        with patch.object(bot.session, "make_request", new=AsyncMock()) as transport:
            await code(incoming, state)
            sent = transport.call_args.args[1]
            assert isinstance(sent, SendMessage) and sent.chat_id == 9925
        await bot.session.close()

    asyncio.run(journey())
