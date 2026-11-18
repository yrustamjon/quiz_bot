from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from apps.accounts.services import register_student
from apps.attempts import services as engine
from asgiref.sync import sync_to_async
from rest_framework.exceptions import APIException

from bot import services
from bot.keyboards.exam import back_menu, menu
from bot.ui import Panel, text_entities

from .presentation import home_text, intro, show_attempt

router = Router()
db = sync_to_async


class Registration(StatesGroup):
    name = State()
    code = State()


@router.message(Command("start", "menu"))
async def start(message: Message, state: FSMContext):
    s = await db(services.student)(message.from_user.id)
    if not s:
        await state.set_state(Registration.name)
        await message.answer("Xush kelibsiz! Ism va familiyangizni kiriting.")
        return
    await state.clear()
    text = home_text(s.full_name)
    await message.answer(text, reply_markup=menu(), entities=text_entities(text))


@router.message(Command("continue"))
async def continue_exam(message: Message, state: FSMContext):
    await state.set_state(None)
    a = await db(engine.resume)(message.from_user.id)
    if not a:
        await message.answer("Faol test topilmadi.", reply_markup=menu())
        return
    await show_attempt(message, a, message.from_user.id)


@router.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Bosh menyuga qaytdingiz. Boshlangan testingiz davom etadi; uning vaqti to‘xtamaydi.",
        reply_markup=menu(),
    )


@router.message(Command("help"))
async def help_message(message: Message):
    text = (
        "Qanday foydalaniladi?\n\n"
        "1. «Test tanlash»dan testni tanlang yoki berilgan kod bilan kiring.\n"
        "2. Shartlarni o‘qib, «Testni boshlash»ni bosing.\n"
        "3. Javobni A, B, C yoki D tugmasi bilan belgilang.\n\n"
        "Testdan chiqib ketsangiz, /continue bilan qaytasiz. Vaqt to‘xtamaydi.\n"
        "Natijalar o‘qituvchi belgilagan vaqtda ko‘rinadi.\n\n"
        "/menu — bosh menyu\n/cancel — kod kiritishni bekor qilish"
    )
    await message.answer(text, entities=text_entities(text), reply_markup=back_menu())


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
    text = "Ro‘yxatdan o‘tdingiz!\n\nTest tanlang yoki o‘qituvchingiz bergan kod bilan kiring."
    await message.answer(text, reply_markup=menu(), entities=text_entities(text))


@router.message(Registration.code, F.text)
async def code(message: Message, state: FSMContext):
    data = await state.get_data()
    target = message
    prompt_id = data.get("code_prompt_id")
    # Only edit our saved prompt in this same private conversation, never the
    # student's code message. Missing/deleted prompts use Panel's safe fallback.
    if isinstance(prompt_id, int) and data.get("code_prompt_chat") == message.chat.id:
        target = Panel(
            Message(message_id=prompt_id, date=message.date, chat=message.chat).as_(
                message.bot
            )
        )
    try:
        q = await db(services.by_code)(message.from_user.id, message.text)
    except APIException:
        await target.answer(
            "Biroz kuting\n\nKod ko‘p marta tekshirildi. Birozdan so‘ng qayta urinib ko‘ring.",
            reply_markup=back_menu(),
        )
        return
    if not q:
        await target.answer(
            "Kod topilmadi\n\nKod noto‘g‘ri, muddati o‘tgan yoki testga kirish yopilgan. O‘qituvchingiz bilan tekshirib, qayta yuboring.",
            reply_markup=back_menu(),
        )
        return
    await state.update_data(code=message.text.strip().upper())
    await state.set_state(None)
    await intro(target, q)
    await state.update_data(code_prompt_id=None, code_prompt_chat=None)


@router.message(F.text)
async def unexpected_text(message: Message, state: FSMContext):
    await start(message, state)
