import logging

from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.types import BufferedInputFile, Message
from apps.attempts import services as engine
from apps.attempts.scoring import percent_display
from asgiref.sync import sync_to_async

from bot import services
from bot.keyboards.exam import keyboard, question_keyboard
from bot.ui import text_chunks, text_entities

db = sync_to_async


def home_text(full_name):
    return (
        f"Salom, {full_name.split()[0]}!\n\n"
        "Yangi test uchun «Test tanlash»ni bosing.\n"
        "O‘qituvchingiz kod bergan bo‘lsa, «Kod bilan kirish»ni tanlang."
    )


def result_text(data, heading="Natijangiz", details=False):
    if not data["released"]:
        return f"{heading}\n\nNatijangiz saqlandi. O‘qituvchi e’lon qilgach shu yerda ko‘rinadi."
    lines = [heading, "", data["title"], ""]
    if "percentage" in data:
        lines.append(f"Natija: {percent_display(data['percentage'])}%")
    if "earned" in data and "maximum" in data:
        lines.append(f"Ball: {data['earned']} / {data['maximum']}")
    counts = [
        f"{label}: {data[key]}"
        for key, label in [
            ("correct", "To‘g‘ri"),
            ("incorrect", "Xato"),
            ("unanswered", "Javobsiz"),
        ]
        if key in data
    ]
    if counts:
        lines.extend(["", "  ·  ".join(counts)])
    if "rank" in data:
        lines.extend(
            [
                "",
                f"Reytingdagi o‘rningiz: {data['rank'] or '—'}",
                "Yangi natijalar bilan o‘rin o‘zgarishi mumkin.",
            ]
        )
    if details and data.get("questions"):
        lines.extend(["", "Javoblar tahlili"])
        for i, q in enumerate(data["questions"], 1):
            selected = (
                q["options"][q["selected"]]
                if q["selected"] is not None
                else "Javob berilmagan"
            )
            lines.extend(
                [
                    f"\n{i}. {q['text']}",
                    f"Sizning javobingiz: {selected}",
                    f"To‘g‘ri javob: {q['options'][q['correct']]}",
                ]
            )
    return "\n".join(lines)


async def show_result(message, a, tid):
    data = await db(engine.student_result)(a, tid)
    text = result_text(data, "Test yakunlandi", details=True)
    rows = []
    if "rank" in data:
        rows.append([("Reytingni ko‘rish", f"quizrank:{a.quiz_id}")])
    rows.append([("📊 Natijalarim", "results"), ("📝 Test tanlash", "list:0")])
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


async def intro(message, q, page=0):
    text = (
        f"{q.title}\n{q.subject}\n\n"
        f"{q.question_count} savol  ·  {q.duration_minutes} daqiqa\n"
        f"Ruxsat etilgan urinishlar: {q.max_attempts}\n\n"
        "Boshlashdan oldin\n"
        "• Vaqt boshlanganidan keyin to‘xtamaydi.\n"
        "• Javoblaringiz avtomatik saqlanadi.\n"
        "• Javobsiz savolga 0 ball beriladi.\n"
        + (
            "• Savollar ketma-ket beriladi; oldingi javob o‘zgarmaydi."
            if q.navigation == "sequential"
            else "• Savollar orasida o‘tish va javobni o‘zgartirish mumkin."
        )
    )
    await message.answer(
        text,
        entities=text_entities(text),
        reply_markup=keyboard(
            [
                [("▶️ Testni boshlash", f"s:{q.pk}", "success")],
                [("‹ Testlarga qaytish", f"list:{page}")]
                if q.access == "public"
                else [],
                [("Bosh menyu", "menu")],
            ]
        ),
    )


async def continue_exam_proxy(message, tid):
    a = await db(engine.resume)(tid)
    if a:
        await show_attempt(message, a, tid)
    else:
        await message.answer(
            "Boshlangan test yo‘q\n\nTestni boshlasangiz, shu bo‘lim orqali unga qaytishingiz mumkin.",
            reply_markup=keyboard(
                [[("📝 Test tanlash", "list:0", "primary")], [("‹ Bosh menyu", "menu")]]
            ),
        )
