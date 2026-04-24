from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import logger
from database import set_psycho_mode, is_psycho_mode

# Импортируй свой AI модуль
try:
    from services.ai import answer as ai_answer
except ImportError:
    async def ai_answer(text):
        return "🤖 AI временно недоступен. Я всё ещё здесь, чтобы выслушать тебя 💙"

router = Router()

class PsychoMode(StatesGroup):
    active = State()

@router.message(F.text == "🧠 Психолог")
async def start_psycho(message: Message, state: FSMContext):
    """Вход в психо-режим"""
    await state.set_state(PsychoMode.active)
    await set_psycho_mode(message.from_user.id, True)
    
    await message.answer(
        "🧠 *Режим психолога активирован*\n\n"
        "Я здесь, чтобы выслушать тебя. "
        "Пиши всё, что чувствуешь — я поддержу 💙\n\n"
        "Чтобы выйти, нажми /menu или кнопку ниже",
        parse_mode="Markdown"
    )

@router.message(PsychoMode.active)
async def psycho_chat(message: Message):
    """Обработка сообщений в психо-режиме"""
    try:
        # Показываем "печатает..."
        await message.chat.action("typing")
        
        # Получаем ответ от AI
        response = await ai_answer(message.text)
        
        await message.answer(
            response,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Psycho mode error: {e}")
        await message.answer(
            "⚠️ *Произошла ошибка*\n\n"
            "AI временно недоступен, но я всё ещё здесь. "
            "Попробуй позже или напиши ещё раз 💙",
            parse_mode="Markdown"
        )

@router.message(F.text == "🗣 Высказаться")
async def exit_psycho(message: Message, state: FSMContext):
    """Выход из психо-режима"""
    await state.clear()
    await set_psycho_mode(message.from_user.id, False)
    
    await message.answer(
        "👋 *Обычный режим*\n\n"
        "Если понадобишься поддержка — я всегда рядом. "
        "Просто нажми 🧠 Психолог",
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "psycho_exit")
async def psycho_exit_callback(callback: CallbackQuery, state: FSMContext):
    """Выход через inline-кнопку"""
    await state.clear()
    await set_psycho_mode(callback.from_user.id, False)
    await callback.message.edit_text("👋 Вышел из режима психолога")
    await callback.answer()