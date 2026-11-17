import asyncio
import logging
import time
import uuid

from aiogram import Router
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from apps.attempts import services as engine
from apps.attempts.scoring import percent_display
from apps.quizzes.models import Quiz
from asgiref.sync import sync_to_async
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import APIException

from bot import services
from bot.keyboards.exam import back_menu, keyboard, menu
from bot.ui import Panel, panel_lock

from .presentation import continue_exam_proxy, intro, show_attempt, show_result
from .registration import Registration

router = Router()
db = sync_to_async


async def acknowledge(c):
    try:
        await asyncio.wait_for(c.answer(), timeout=5)
    except (TelegramAPIError, TimeoutError):
        logging.getLogger(__name__).info("Telegram acknowledgement unavailable")


@router.callback_query()
async def callback(c: CallbackQuery, state: FSMContext):
    # Acknowledge the tap while SQL/rendering runs, instead of serializing two
    # network roundtrips before the student sees the next screen.
    started = time.monotonic()
    ack = asyncio.create_task(acknowledge(c))
    try:
        if not isinstance(c.message, Message):
            await c.bot.send_message(
                c.from_user.id, "Xabar mavjud emas. /continue orqali davom eting."
            )
            return
        lock = panel_lock(c.message)
        async with lock:
            await handle_callback(c, state, Panel(c.message, lock=lock))
    finally:
        rendered = time.monotonic()
        await ack
        action = (c.data or "").split(":", 1)[0]
        kind = (
            action
            if action
            in {
                "menu",
                "code",
                "profile",
                "results",
                "quizrank",
                "ranking",
                "list",
                "q",
                "s",
                "a",
                "n",
                "f",
                "yes",
                "resume",
            }
            else "unknown"
        )
        logging.getLogger(__name__).info(
            "Bot interaction kind=%s render_ms=%d total_ms=%d",
            kind,
            round((rendered - started) * 1000),
            round((time.monotonic() - started) * 1000),
        )


async def handle_callback(c, state, message):
    tid = c.from_user.id
    data = c.data or ""
    parts = data.split(":")
    try:
        s = await db(services.student)(tid)
        if not s:
            await message.answer("Avval /start orqali ro‘yxatdan o‘ting.")
            return
        if data == "resume":
            await continue_exam_proxy(message, tid)
            return
        if data == "menu":
            await state.clear()
            await message.answer(
                "QUIZ BOT\n\nTest tanlang yoki boshlangan imtihonni davom ettiring.",
                reply_markup=menu(),
            )
            return
        if data == "code":
            await state.set_state(Registration.code)
            await message.answer(
                "🔑 TEST KODI\n\nO‘qituvchingiz bergan 10 belgili kodni yuboring.\nMasalan: AB12CD34EF",
                reply_markup=back_menu(),
            )
            return
        if data == "profile":
            await message.answer(
                "👤 PROFIL\n\n" + s.full_name, reply_markup=back_menu()
            )
            return
        if parts[0] == "results":
            page = max(0, min(10000, int(parts[1]) if len(parts) > 1 else 0))
            result, total = await db(services.result_page)(tid, page)
            rows = []
            navigation = []
            if page:
                navigation.append(("← Oldingi", f"results:{page - 1}"))
            if page + 1 < total:
                navigation.append(("Keyingi →", f"results:{page + 1}"))
            if navigation:
                rows.append(navigation)
            rows.append([("‹ Bosh menyu", "menu")])
            if result is None:
                text = "📊 NATIJALARIM\n\nHali yakunlangan test yo‘q. Testni tugatganingizdan keyin natija shu yerda ko‘rinadi."
            elif not result.get("released"):
                text = f"📊 NATIJALARIM · {page + 1}/{total}\n\nNatija saqlandi. O‘qituvchi e’lon qilgach shu yerda ochiladi."
            else:
                text = (
                    f"📊 NATIJALARIM · {page + 1}/{total}\n\n"
                    + result["title"]
                    + "\n\n"
                )
                for key, label in [
                    ("earned", "Ball"),
                    ("maximum", "Maksimum"),
                    ("percentage", "Natija (%)"),
                    ("correct", "To‘g‘ri"),
                    ("incorrect", "Noto‘g‘ri"),
                    ("unanswered", "Javobsiz"),
                    ("rank", "Reyting"),
                ]:
                    if key in result:
                        text += f"{label}: {percent_display(result[key]) if key == 'percentage' else result[key]}\n"
            await message.answer(text[:3800], reply_markup=keyboard(rows))
            return
        if parts[0] == "quizrank":
            result = await db(services.quiz_ranking)(tid, int(parts[1]))
            if result is None:
                await message.answer("Reytingga kirish huquqi yo‘q.")
                return
            rows, own = result
            text = (
                "Test reytingi (o‘zgarishi mumkin):\n"
                + "\n".join(
                    f"{r['rank']}. {r['name']}"
                    + (f" — {r['percentage']}%" if r["percentage"] is not None else "")
                    for r in rows
                )
                + f"\nSizning o‘rningiz: {own or '—'}"
            )
            await message.answer(text, reply_markup=back_menu())
            return
        if data == "ranking":
            rows, own = await db(services.student_ranking)(tid)
            await message.answer(
                "🏆 REYTING\n\n"
                + "\n".join(
                    f"{x['rank']}. {x['name']} — {x['percentage']}%" for x in rows
                )
                + (
                    f"\n\nSizning o‘rningiz: {own or '—'}\nReyting yangi natijalar bilan yangilanadi."
                    if rows
                    else "Hali yakunlangan natijalar yo‘q.\nTestni tugatgach reytingda qatnashasiz."
                ),
                reply_markup=back_menu(),
            )
            return
        if parts[0] == "list":
            page = max(0, min(10000, int(parts[1])))
            quizzes = await db(services.public_quizzes)(page)
            visible = quizzes[: services.PUBLIC_PAGE_SIZE]
            text = f"📝 OCHIQ TESTLAR\n{page + 1}-sahifa · Test raqamini tanlang\n"
            for index, quiz in enumerate(visible, 1):
                text += f"\n{index}. {quiz.title}\n    {quiz.question_count} savol · {quiz.duration_minutes} daq · {quiz.max_attempts} urinish\n"
            rows = []
            if visible:
                rows.append(
                    [(str(i), f"q:{quiz.pk}") for i, quiz in enumerate(visible, 1)]
                )
            else:
                text = "📝 OCHIQ TESTLAR\n\nHozircha ochiq test yo‘q. O‘qituvchingiz kod bergan bo‘lsa, Test kodi bo‘limidan foydalaning."
            navigation = []
            if page:
                navigation.append(("← Oldingi", f"list:{page - 1}"))
            if len(quizzes) > services.PUBLIC_PAGE_SIZE:
                navigation.append(("Keyingi →", f"list:{page + 1}"))
            if navigation:
                rows.append(navigation)
            rows.append([("🔑 Test kodi", "code"), ("‹ Bosh menyu", "menu")])
            await message.answer(text, reply_markup=keyboard(rows))
            return
        if parts[0] in ["q", "s"]:
            q = await db(Quiz.objects.get)(pk=int(parts[1]))
            cached = (await state.get_data()).get("code")
            await db(engine.access_quiz)(s, q, cached)
            if parts[0] == "q":
                await intro(message, q)
                return
            a = await db(engine.start)(s, q, cached)
            await show_attempt(message, a, tid)
            return
        aid = uuid.UUID(hex=parts[1])
        if parts[0] == "a":
            a, _ = await db(engine.answer)(
                aid, tid, int(parts[2]), int(parts[3]), int(parts[4])
            )
            await show_attempt(message, a, tid)
        elif parts[0] == "n":
            a = await db(engine.navigate)(aid, tid, int(parts[2]), int(parts[3]))
            await show_attempt(message, a, tid)
        elif parts[0] == "f":
            a, total, answered = await db(engine.preview_finish)(aid, tid)
            if a.status != "in_progress":
                await show_result(message, a, tid)
                return
            await message.answer(
                f"TESTNI YAKUNLASH\n\n{answered}/{total} javob saqlangan.\n{total - answered} ta savol javobsiz — ularga 0 ball.\n\nYakunlangandan keyin javoblar o‘zgarmaydi.\nDavom etasizmi yoki yakunlaysizmi?",
                reply_markup=keyboard(
                    [
                        [
                            ("← Davom etish", "resume", "primary"),
                            ("Ha, yakunlash", "yes:" + aid.hex, "danger"),
                        ]
                    ]
                ),
            )
        elif parts[0] == "yes":
            a = await db(engine.finish)(aid, tid, True)
            await show_result(message, a, tid)
    except (APIException, ObjectDoesNotExist, ValueError, IndexError):
        await message.answer(
            "Amal eskirgan, muddat tugagan yoki ruxsat yo‘q. /continue orqali davom eting."
        )


@router.errors()
async def recover_update(event):
    """Keep one failed update from terminating polling; never log its payload."""
    logging.getLogger(__name__).error(
        "Bot update failed: %s", type(event.exception).__name__
    )
    update = event.update
    message = update.message or (
        update.callback_query.message if update.callback_query else None
    )
    if isinstance(message, Message):
        try:
            await message.answer(
                "Xizmat vaqtincha mavjud emas. Javoblaringiz bazada saqlanadi. Birozdan so‘ng /continue orqali qayta urinib ko‘ring."
            )
        except TelegramAPIError:
            pass
    return True
