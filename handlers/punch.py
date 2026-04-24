from aiogram import Router
from aiogram.types import Message

router = Router()
sessions = {}

@router.message(lambda m: m.text == "🥊 Груша")
async def start_punch(m: Message):
    sessions[m.from_user.id] = True
    await m.answer("Можешь выговориться. Я слушаю.")

@router.message()
async def punch_chat(m: Message):
    if sessions.get(m.from_user.id):
        await m.answer("Понимаю... продолжай")