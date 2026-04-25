from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import logger
from database import set_psycho, get_user
from services.ai_router import generate

router = Router()
class PsychoState(StatesGroup): active = State()

@router.message(F.text == "🧠 Психолог")
async def start_psycho(m: Message, state: FSMContext):
    await state.set_state(PsychoState.active)
    await set_psycho(m.from_user.id, True)
    await m.answer("🧠 Я рядом. Пиши, что чувствуешь.\n_Для выхода: /menu_", parse_mode="Markdown")

@router.message(PsychoState.active)
async def psycho_chat(m: Message):
    try:
        u = await get_user(m.from_user.id)
        resp = await generate(m.text, f"Ты — эмпатичный психолог. Поддержи пользователя ({u.get('role') if u else 'user'}). Будь краток и тёпел.", task_type="psycho")
        await m.answer(resp, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Psycho err: {e}")
        await m.answer("💙 Я слушаю. Попробуй ещё раз.")

@router.message(F.text == "🗣 Высказаться")
async def exit_psycho(m: Message, state: FSMContext):
    await state.clear()
    await set_psycho(m.from_user.id, False)
    await m.answer("👋 Обычный режим. Я всегда на связи.")