# handlers/psycho.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import logger
from database import set_psycho_mode, is_psycho_mode, get_user
from services.ai_router import generate

router = Router()

class PsychoMode(StatesGroup):
    """Состояния психо-режима"""
    active = State()
    clarifying = State()  # для уточняющих вопросов (можно расширить)

@router.message(F.text == "🧠 Психолог")
async def start_psycho(message: Message, state: FSMContext):
    """Вход в психо-режим"""
    await state.set_state(PsychoMode.active)
    await set_psycho_mode(message.from_user.id, True)
    
    await message.answer(
        "🧠 *Режим психолога активирован*\n\n"
        "Я здесь, чтобы выслушать тебя без осуждения. "
        "Пиши всё, что чувствуешь — я поддержу 💙\n\n"
        "*Чтобы выйти:* нажми /menu или кнопку ниже",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔚 Выйти из режима", callback_data="psycho_exit")]
        ]),
        parse_mode="Markdown"
    )
    logger.info(f"🧠 Psycho mode ON for {message.from_user.id}")

@router.message(PsychoMode.active, F.text != "🗣 Высказаться")
async def psycho_chat(message: Message, state: FSMContext):
    """Обработка сообщений в психо-режиме"""
    try:
        # Показываем "печатает..."
        await message.chat.action("typing")
        
        # Получаем контекст пользователя
        user = await get_user(message.from_user.id)
        user_name = user.get("first_name") if user else None
        user_role = user.get("role") if user else "user"
        
        # Системный промпт с контекстом
        system_prompt = (
            f"Ты — эмпатичный семейный психолог-бот. "
            f"Пользователь: {user_role}. "
            f"Твоя задача: выслушать, поддержать, задать уточняющий вопрос если нужно. "
            f"НЕ давай прямых советов 'сделай то-то'. "
            f"Используй 'Я-сообщения' и валидацию чувств. "
            f"Будь тёплым, но не навязчивым. Ответь на русском."
        )
        
        # Генерируем ответ через AI router
        response = await generate(
            prompt=message.text,
            system=system_prompt,
            task_type="psycho",
            user_name=user_name
        )
        
        await message.answer(
            response,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔚 Выйти", callback_data="psycho_exit")]
            ])
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
@router.callback_query(F.data == "psycho_exit")
async def exit_psycho(event: Message | CallbackQuery, state: FSMContext):
    """Выход из психо-режима (универсальный хендлер)"""
    user_id = event.from_user.id if hasattr(event, 'from_user') else event.message.from_user.id
    
    await state.clear()
    await set_psycho_mode(user_id, False)
    
    response_text = (
        "👋 *Обычный режим*\n\n"
        "Если понадобишься поддержка — я всегда рядом. "
        "Просто нажми 🧠 Психолог"
    )
    
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(response_text, parse_mode="Markdown")
        await event.answer()
    else:
        await event.answer(response_text, parse_mode="Markdown")
    
    logger.info(f"🧠 Psycho mode OFF for {user_id}")