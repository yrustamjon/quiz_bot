import logging
import uuid

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from apps.accounts.services import register_student
from apps.attempts import services as engine
from apps.quizzes.models import Quiz
from asgiref.sync import sync_to_async
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import APIException

from bot import services
from bot.keyboards.exam import keyboard, menu, question_keyboard

router = Router()
db = sync_to_async


class Registration(StatesGroup):
    name = State()
    code = State()


async def show_result(message, a, tid):
    data = await db(engine.student_result)(a, tid)
    if not data["released"]:
        await message.answer(
            "Natijangiz saqlandi. Natijalar keyinroq e’lon qilinadi.",
            reply_markup=menu(),
        )
        return
    lines = ["Test yakunlandi!", data["title"]]
    for key, label in [
        ("earned", "Ball"),
        ("maximum", "Maksimum"),
        ("percentage", "Natija (%)"),
        ("correct", "To‘g‘ri"),
        ("incorrect", "Noto‘g‘ri"),
        ("unanswered", "Javobsiz"),
    ]:
        if key in data:
            lines.append(f"{label}: {data[key]}")
    if data.get("questions"):
        for q in data["questions"]:
            lines.append(q["text"] + " — " + q["options"][q["correct"]])
    text = "\n".join(lines)
    for i in range(0, len(text), 3800):
        await message.answer(text[i : i + 3800])
    await message.answer("Bosh menyu", reply_markup=menu())


async def show_attempt(message, a, tid):
    if a.status != "in_progress":
        await show_result(message, a, tid)
        return
    q = await db(services.get_question)(a)
    if not q:
        await message.answer(
            "Barcha javoblar saqlandi. Yakunlashni tasdiqlang.",
            reply_markup=keyboard([[("Testni yakunlash", "f:" + a.id.hex)]]),
        )
        return
    from django.utils import timezone

    remaining = max(0, int((a.deadline - timezone.now()).total_seconds()))
    count = await db(a.questions.count)()
    text = (
        f"{a.quiz.title}\nSavol {q.position + 1}/{count} · Qolgan vaqt: {remaining // 60}:{remaining % 60:02d}\n\n{q.text}\n\n"
        + "\n".join(f"{'ABCD'[i]}) {value}" for i, value in enumerate(q.options))
    )
    markup = await db(question_keyboard)(a, q)
    image = await db(services.image_data)(q.image_name)
    if image:
        try:
            if len(text) <= 1024:
                await message.answer_photo(
                    BufferedInputFile(image, filename="savol.png"),
                    caption=text,
                    reply_markup=markup,
                )
                return
            await message.answer_photo(BufferedInputFile(image, filename="savol.png"))
        except TelegramAPIError:
            logging.getLogger(__name__).warning("Question image delivery failed")
    for i in range(0, len(text), 3800):
        await message.answer(
            text[i : i + 3800], reply_markup=markup if i + 3800 >= len(text) else None
        )


@router.message(Command("start", "menu", "help"))
async def start(message: Message, state: FSMContext):
    s = await db(services.student)(message.from_user.id)
    if not s:
        await state.set_state(Registration.name)
        await message.answer("Xush kelibsiz! Ism va familiyangizni kiriting.")
        return
    await state.clear()
    await message.answer(
        "Quiz Bot — test tanlang. Vaqt test davomida to‘xtamaydi.", reply_markup=menu()
    )


@router.message(Command("continue"))
async def continue_exam(message: Message):
    a = await db(engine.resume)(message.from_user.id)
    if not a:
        await message.answer("Faol test topilmadi.", reply_markup=menu())
        return
    await show_attempt(message, a, message.from_user.id)


@router.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Suhbat amali bekor qilindi. Faol test va uning vaqti saqlanadi. /continue bilan davom eting.",
        reply_markup=menu(),
    )


@router.message(Registration.name, F.text)
async def name(message: Message, state: FSMContext):
    try:
        await db(register_student)(
            message.from_user.id, message.text, message.from_user.username or ""
        )
    except APIException:
        await message.answer("Ism va familiyani 3–150 belgi bilan kiriting.")
        return
    await state.clear()
    await message.answer("Ro‘yxatdan o‘tdingiz.", reply_markup=menu())


@router.message(Registration.code, F.text)
async def code(message: Message, state: FSMContext):
    try:
        q = await db(services.by_code)(message.from_user.id, message.text)
    except APIException:
        await message.answer("Ko‘p urinish. Keyinroq qayta urinib ko‘ring.")
        return
    if not q:
        await message.answer("Kod noto‘g‘ri yoki muddati o‘tgan.")
        return
    await state.update_data(code=message.text.strip().upper())
    await intro(message, q)


async def intro(message, q):
    text = f"{q.title}\n{q.subject} · {q.question_count} savol · {q.duration_minutes} daqiqa\nUrinishlar: {q.max_attempts} · Rejim: {q.navigation}\nVaqt Telegram yopilsa ham davom etadi. Javoblar saqlanadi. Javobsiz savollar 0 ball. Yakunlash tasdiqlanadi."
    await message.answer(
        text,
        reply_markup=keyboard(
            [[("Testni boshlash", f"s:{q.pk}")], [("Bosh menyu", "menu")]]
        ),
    )


@router.callback_query()
async def callback(c: CallbackQuery, state: FSMContext):
    await c.answer()
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
                await c.message.answer(
                    "\n".join(f"{k}: {v}" for k, v in r.items() if k != "questions")[
                        :3800
                    ]
                )
            if not results:
                await c.message.answer("Hozircha natijalar yo‘q.")
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
                [(f"{q.title[:40]} · {q.duration_minutes} daq", f"q:{q.pk}")]
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


async def continue_exam_proxy(message, tid):
    a = await db(engine.resume)(tid)
    if a:
        await show_attempt(message, a, tid)
    else:
        await message.answer("Faol test yo‘q.", reply_markup=menu())
