from aiogram import Router
from aiogram.types import Message
from database import execute

router = Router()

@router.message(lambda m: m.text.startswith("/remind"))
async def remind(m: Message):
    await m.answer("Напоминание добавлено (упрощённо)")

@router.message(lambda m: m.text == "🛒 Список")
async def shopping(m: Message):
    await m.answer("Список пока пуст")