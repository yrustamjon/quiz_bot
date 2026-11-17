import logging
import uuid

from aiogram import Router
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from apps.attempts import services as engine
from apps.attempts.scoring import percent_display
from apps.quizzes.models import Quiz
from asgiref.sync import sync_to_async
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import APIException

from bot import services
from bot.keyboards.exam import keyboard, menu

from .presentation import continue_exam_proxy, intro, show_attempt, show_result
from .registration import Registration

router = Router()
db = sync_to_async


@router.callback_query()
async def callback(c: CallbackQuery, state: FSMContext):
    try:
        await c.answer()
    except TelegramBadRequest:
        logging.getLogger(__name__).info("Stale Telegram acknowledgement")
    if not isinstance(c.message, Message):
        await c.bot.send_message(
            c.from_user.id, "Xabar mavjud emas. /continue orqali davom eting."
        )
        return
    tid = c.from_user.id
    data = c.data or ""
    parts = data.split(":")
    try:
        s = await db(services.student)(tid)
        if not s:
            await c.message.answer("Avval /start orqali ro‘yxatdan o‘ting.")
            return
        if data == "resume":
            await continue_exam_proxy(c.message, tid)
            return
        if data == "menu":
            await state.clear()
            await c.message.answer("Bosh menyu", reply_markup=menu())
            return
        if data == "code":
            await state.set_state(Registration.code)
            await c.message.answer("Test kodini kiriting.")
            return
        if data == "profile":
            await c.message.answer(s.full_name, reply_markup=menu())
            return
        if data == "results":
            results = await db(services.own_results)(tid)
            for r in results:
                if not r.get("released"):
                    await c.message.answer(
                        "Natijangiz saqlandi. Natijalar keyinroq e’lon qilinadi."
                    )
                    continue
                labels = {
                    "title": "Test",
                    "earned": "Ball",
                    "maximum": "Maksimum",
                    "percentage": "Natija (%)",
                    "correct": "To‘g‘ri",
                    "incorrect": "Noto‘g‘ri",
                    "unanswered": "Javobsiz",
                    "rank": "Reyting (o‘zgarishi mumkin)",
                }
                await c.message.answer(
                    "\n".join(
                        f"{label}: {percent_display(r[key]) if key == 'percentage' else r[key]}"
                        for key, label in labels.items()
                        if key in r
                    )[:3800]
                )
            if not results:
                await c.message.answer("Hozircha natijalar yo‘q.")
            return
        if parts[0] == "quizrank":
            result = await db(services.quiz_ranking)(tid, int(parts[1]))
            if result is None:
                await c.message.answer("Reytingga kirish huquqi yo‘q.")
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
            await c.message.answer(text, reply_markup=menu())
            return
        if data == "ranking":
            rows, own = await db(services.student_ranking)(tid)
            await c.message.answer(
                "Reyting (o‘zgarishi mumkin):\n"
                + "\n".join(
                    f"{x['rank']}. {x['name']} — {x['percentage']}%" for x in rows
                )
                + f"\nSizning o‘rningiz: {own or '—'}",
                reply_markup=menu(),
            )
            return
        if parts[0] == "list":
            page = int(parts[1])
            page = max(0, min(10000, page))
            quizzes = await db(services.public_quizzes)(page)
            rows = [
                [
                    (
                        f"{q.title[:30]} · {q.question_count} savol · {q.duration_minutes} daq · {q.max_attempts} urinish",
                        f"q:{q.pk}",
                    )
                ]
                for q in quizzes[:8]
            ]
            if len(quizzes) > 8:
                rows.append([("Keyingi", f"list:{page + 1}")])
            if page:
                rows.append([("Oldingi", f"list:{page - 1}")])
            rows.append([("Bosh menyu", "menu")])
            await c.message.answer(
                "Ochiq testlar" if quizzes else "Hozircha ochiq test yo‘q.",
                reply_markup=keyboard(rows),
            )
            return
        if parts[0] in ["q", "s"]:
            q = await db(Quiz.objects.get)(pk=int(parts[1]))
            cached = (await state.get_data()).get("code")
            await db(engine.access_quiz)(s, q, cached)
            if parts[0] == "q":
                await intro(c.message, q)
                return
            a = await db(engine.start)(s, q, cached)
            await show_attempt(c.message, a, tid)
            return
        aid = uuid.UUID(hex=parts[1])
        if parts[0] == "a":
            a, _ = await db(engine.answer)(
                aid, tid, int(parts[2]), int(parts[3]), int(parts[4])
            )
            await show_attempt(c.message, a, tid)
        elif parts[0] == "n":
            a = await db(engine.navigate)(aid, tid, int(parts[2]), int(parts[3]))
            await show_attempt(c.message, a, tid)
        elif parts[0] == "f":
            from apps.attempts.models import Attempt

            a = await db(Attempt.objects.select_related("student").get)(pk=aid)
            await db(engine.check_owner)(a, tid)
            await c.message.answer(
                "Testni yakunlamoqchimisiz? Javob berilmagan savollar uchun 0 ball beriladi. Yakunlangandan keyin testga qayta olmaysiz.",
                reply_markup=keyboard(
                    [
                        [("Ha, yakunlash", "yes:" + aid.hex)],
                        [("Yo‘q, davom etish", "resume")],
                    ]
                ),
            )
        elif parts[0] == "yes":
            a = await db(engine.finish)(aid, tid, True)
            await show_result(c.message, a, tid)
    except (APIException, ObjectDoesNotExist, ValueError, IndexError):
        await c.message.answer(
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
