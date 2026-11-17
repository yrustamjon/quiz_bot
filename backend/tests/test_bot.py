import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from apps.attempts.models import Attempt

from bot.handlers.main import callback
from bot.keyboards.exam import question_keyboard


@pytest.mark.django_db(transaction=True)
def test_manipulated_callback_does_not_crash():
    from apps.accounts.models import StudentProfile

    StudentProfile.objects.create(telegram_id=321, full_name="Bot Test")
    from aiogram.types import Message

    message = MagicMock(spec=Message)
    message.answer = AsyncMock()
    c = SimpleNamespace(
        from_user=SimpleNamespace(id=321),
        data="a:invalid:0:0:0",
        answer=AsyncMock(),
        message=message,
    )
    asyncio.run(callback(c, SimpleNamespace()))
    c.answer.assert_awaited_once()
    message.answer.assert_awaited_once()
    assert Attempt.objects.count() == 0


def test_callback_size_and_no_answer_key():
    import uuid

    a = SimpleNamespace(
        id=uuid.uuid4(), revision=123, cursor=1, navigation="sequential"
    )
    q = SimpleNamespace(position=1, correct_option=2)
    markup = question_keyboard(a, q)
    for row in markup.inline_keyboard:
        for button in row:
            assert len(button.callback_data.encode()) <= 64
    assert [b.text for b in markup.inline_keyboard[0]] == list("ABCD")


@pytest.mark.django_db(transaction=True)
def test_real_exam_services_through_aiogram_callbacks(teacher):
    from aiogram.types import Message
    from apps.accounts.models import StudentProfile
    from apps.attempts.models import AttemptAnswer
    from apps.questions.models import Question, QuizQuestion
    from apps.quizzes.models import Quiz
    from apps.quizzes.services import transition

    student = StudentProfile.objects.create(telegram_id=5544, full_name="Bot Journey")
    quiz = Quiz.objects.create(
        owner=teacher, title="Bot Journey", subject="Fan", question_count=1
    )
    question = Question.objects.create(
        owner=teacher, text="2+2?", options=["3", "4", "5", "6"], correct_option=1
    )
    QuizQuestion.objects.create(quiz=quiz, question=question, position=0)
    transition(quiz, "published")
    message = MagicMock(spec=Message)
    message.answer = AsyncMock()
    c = SimpleNamespace(
        from_user=SimpleNamespace(id=student.telegram_id),
        data=f"s:{quiz.pk}",
        answer=AsyncMock(),
        message=message,
    )
    state = SimpleNamespace(get_data=AsyncMock(return_value={}))
    asyncio.run(callback(c, state))
    attempt = Attempt.objects.get(student=student)
    c.data = f"a:{attempt.id.hex}:0:1:0"
    asyncio.run(callback(c, state))
    assert AttemptAnswer.objects.filter(question__attempt=attempt).count() == 1
    c.data = "f:" + attempt.id.hex
    asyncio.run(callback(c, state))
    assert any(
        "Testni yakunlamoqchimisiz?" in str(call)
        for call in message.answer.call_args_list
    )
    c.data = "yes:" + attempt.id.hex
    asyncio.run(callback(c, state))
    attempt.refresh_from_db()
    assert attempt.status == "completed" and attempt.percentage == 100
    asyncio.run(callback(c, state))
    attempt.refresh_from_db()
    assert attempt.correct == 1


@pytest.mark.django_db(transaction=True)
def test_registration_private_code_and_real_image_service(teacher):
    import io

    from aiogram.types import Message
    from apps.accounts.models import StudentProfile
    from apps.questions.models import Question, QuizQuestion
    from apps.quizzes.models import Quiz
    from apps.quizzes.services import transition
    from django.core.files.base import ContentFile
    from PIL import Image

    from bot.handlers.registration import code, name

    message = MagicMock(spec=Message)
    message.answer = AsyncMock()
    message.answer_photo = AsyncMock()
    message.from_user = SimpleNamespace(id=6199, username="optional_name")
    message.text = "O‘quvchi Sinovi"
    state = SimpleNamespace(clear=AsyncMock(), update_data=AsyncMock())
    asyncio.run(name(message, state))
    assert StudentProfile.objects.filter(telegram_id=6199).count() == 1
    quiz = Quiz.objects.create(
        owner=teacher,
        title="Rasmli yopiq test",
        subject="Fan",
        question_count=1,
        access="private",
    )
    question = Question.objects.create(
        owner=teacher,
        text="Rasmli savol",
        options=["a", "b", "c", "d"],
        correct_option=2,
    )
    data = io.BytesIO()
    Image.new("RGB", (10, 10)).save(data, format="PNG")
    question.image.save("image.png", ContentFile(data.getvalue()))
    QuizQuestion.objects.create(quiz=quiz, question=question, position=0)
    transition(quiz, "published")
    quiz.refresh_from_db()
    message.text = quiz.access_code.code
    asyncio.run(code(message, state))
    state.update_data.assert_awaited_with(code=quiz.access_code.code)
    state.get_data = AsyncMock(return_value={"code": quiz.access_code.code})
    c = SimpleNamespace(
        from_user=message.from_user,
        data=f"s:{quiz.pk}",
        answer=AsyncMock(),
        message=message,
    )
    asyncio.run(callback(c, state))
    message.answer_photo.assert_awaited_once()
    call = message.answer_photo.call_args
    assert "Rasmli savol" in call.kwargs["caption"]
    assert call.args[0].filename == "savol.png"
