import logging

from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.types import BufferedInputFile, Message
from apps.attempts import services as engine
from apps.attempts.scoring import percent_display
from asgiref.sync import sync_to_async

from bot import services
from bot.keyboards.exam import back_menu, keyboard, menu, question_keyboard
from bot.ui import text_chunks, text_entities

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
    rows = []
    if "rank" in data:
        rows.append([("Reytingni ko‘rish", f"quizrank:{a.quiz_id}")])
    rows.append([("Bosh menyu", "menu")])
    chunks = list(text_chunks(text))
    for i, chunk in enumerate(chunks):
        await message.answer(
            chunk,
            entities=text_entities(chunk),
            reply_markup=keyboard(rows) if i == len(chunks) - 1 else None,
        )


async def question_photo(message, name, text, markup):
    if not name:
        return False
    bot_id = message.bot.id
    cached = await db(services.photo_file_id)(bot_id, name)
    caption_fits = len(text.encode("utf-16-le")) // 2 <= 1024

    async def deliver(photo):
        return await message.answer_photo(
            photo,
            caption=text if caption_fits else None,
            caption_entities=text_entities(text) if caption_fits else None,
            reply_markup=markup if caption_fits else None,
        )

    if cached:
        try:
            result = await deliver(cached)
        except TelegramBadRequest as error:
            if not any(
                term in error.message.lower()
                for term in ["file identifier", "file_id", "file reference"]
            ):
                raise
            await db(services.forget_photo)(bot_id, name)
            cached = None
    if not cached:
        image = await db(services.image_data)(name)
        if not image:
            return False
        result = await deliver(BufferedInputFile(image, filename="savol.png"))
    if isinstance(result, Message) and result.photo:
        await db(services.remember_photo)(bot_id, name, result.photo[-1].file_id)
    return caption_fits


async def show_attempt(message, a, tid):
    if a.status != "in_progress":
        await show_result(message, a, tid)
        return
    q, count, answered = await db(services.question_view)(a)
    if not q:
        await message.answer(
            "Barcha javoblar saqlandi. Yakunlashni tasdiqlang.",
            reply_markup=keyboard([[("Testni yakunlash", "f:" + a.id.hex)]]),
        )
        return
    from django.utils import timezone

    remaining = max(0, int((a.deadline - timezone.now()).total_seconds()))
    text = (
        f"{a.quiz.title}\n\nSavol {q.position + 1}/{count}  ·  ⏱ {remaining // 60}:{remaining % 60:02d}\n{'▰' * min(10, (answered * 10 // count))}{'▱' * (10 - min(10, answered * 10 // count))}  {answered} javob saqlandi\n\n{q.text}\n\n"
        + "\n".join(f"{'ABCD'[i]}) {value}" for i, value in enumerate(q.options))
    )
    markup = question_keyboard(
        a, q, count=count, selected=q.answer.option if hasattr(q, "answer") else None
    )
    try:
        if await question_photo(message, q.image_name, text, markup):
            return
    except TelegramAPIError:
        logging.getLogger(__name__).warning("Question image delivery failed")
    chunks = list(text_chunks(text))
    for i, chunk in enumerate(chunks):
        await message.answer(
            chunk,
            entities=text_entities(chunk),
            reply_markup=markup if i == len(chunks) - 1 else None,
        )


async def intro(message, q):
    text = (
        f"📝 {q.title}\n{q.subject}\n\nSavollar: {q.question_count}  ·  Vaqt: {q.duration_minutes} daqiqa\nUrinishlar: {q.max_attempts}  ·  {'Ketma-ket' if q.navigation == 'sequential' else 'Erkin'} rejim\n\n⏱ Vaqt test boshlangandan keyin to‘xtamaydi.\nJavoblar saqlanadi. Javobsiz savollar — 0 ball.\n"
        + (
            "Oldingi javobni o‘zgartirib bo‘lmaydi.\n"
            if q.navigation == "sequential"
            else "Vaqt tugaguncha javobni o‘zgartirishingiz mumkin.\n"
        )
        + "Yakunlashdan oldin tasdiqlash so‘raladi."
    )
    await message.answer(
        text,
        entities=text_entities(text),
        reply_markup=keyboard(
            [
                [("▶️ Boshlash", f"s:{q.pk}", "success")],
                [("‹ Testlar", "list:0"), ("Bosh menyu", "menu")],
            ]
        ),
    )


async def continue_exam_proxy(message, tid):
    a = await db(engine.resume)(tid)
    if a:
        await show_attempt(message, a, tid)
    else:
        await message.answer(
            "▶️ DAVOM ETTIRISH\n\nFaol test yo‘q. Yangi test tanlashingiz mumkin.",
            reply_markup=back_menu(),
        )
