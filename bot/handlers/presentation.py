import logging

from aiogram.exceptions import TelegramAPIError
from aiogram.types import BufferedInputFile
from apps.attempts import services as engine
from apps.attempts.scoring import percent_display
from asgiref.sync import sync_to_async

from bot import services
from bot.keyboards.exam import keyboard, menu, question_keyboard

db = sync_to_async


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
        ("rank", "Reyting (o‘zgarishi mumkin)"),
    ]:
        if key in data:
            lines.append(
                f"{label}: {percent_display(data[key]) if key == 'percentage' else data[key]}"
            )
    if data.get("questions"):
        for q in data["questions"]:
            lines.append(q["text"] + " — " + q["options"][q["correct"]])
    text = "\n".join(lines)
    for i in range(0, len(text), 3800):
        await message.answer(text[i : i + 3800])
    rows = []
    if "rank" in data:
        rows.append([("Reytingni ko‘rish", f"quizrank:{a.quiz_id}")])
    rows.append([("Bosh menyu", "menu")])
    await message.answer("Natija saqlandi.", reply_markup=keyboard(rows))


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


async def intro(message, q):
    text = f"{q.title}\n{q.subject} · {q.question_count} savol · {q.duration_minutes} daqiqa\nUrinishlar: {q.max_attempts} · Rejim: {'Ketma-ket' if q.navigation == 'sequential' else 'Erkin'}\nVaqt Telegram yopilsa ham davom etadi; vaqt tugagach test yakunlanadi. Javoblar saqlanadi. Ketma-ket rejimda oldingi javob o‘zgartirilmaydi. Javobsiz savollar 0 ball. Erta yakunlash tasdiqlanadi."
    await message.answer(
        text,
        reply_markup=keyboard(
            [[("Testni boshlash", f"s:{q.pk}")], [("Bosh menyu", "menu")]]
        ),
    )


async def continue_exam_proxy(message, tid):
    a = await db(engine.resume)(tid)
    if a:
        await show_attempt(message, a, tid)
    else:
        await message.answer("Faol test yo‘q.", reply_markup=menu())
