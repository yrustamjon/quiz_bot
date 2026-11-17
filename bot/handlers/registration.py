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
from bot.keyboards.exam import menu

from .presentation import intro, show_attempt

router = Router()
db = sync_to_async


class Registration(StatesGroup):
    name = State()
    code = State()


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
