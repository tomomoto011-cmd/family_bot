from aiogram import Router
from aiogram.types import Message
from services.ai import answer

router = Router()

@router.message(lambda m: m.text == "🧠 Психо")
async def start_psycho(m: Message):
    await m.answer("Напиши, что чувствуешь")

@router.message()
async def psycho_chat(m: Message):
    res = await answer(m.text)
    await m.answer(res)