from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import logger
from database import set_psycho, get_user, is_psycho
from services.ai_router import generate

router = Router()

class PsychoState(StatesGroup):
    active = State()
    clarifying = State()

@router.message(F.text == "🧠 Психолог")
async def start_psycho(m: Message, state: FSMContext):
    await state.set_state(PsychoState.active)
    await set_psycho(m.from_user.id, True)
    logger.info(f"🧠 Psycho ON: {m.from_user.id}")
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔚 Выйти из режима", callback_data="psycho_exit")]
    ])
    
    await m.answer(
        "🧠 *Режим психолога активирован*\n\n"
        "Я здесь, чтобы выслушать тебя без осуждения. "
        "Пиши всё, что чувствуешь — я поддержу 💙\n\n"
        "*Чтобы выйти:* нажми /menu или кнопку ниже",
        reply_markup=kb,
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "psycho_exit")
async def psycho_exit_cb(c: CallbackQuery, state: FSMContext):
    await state.clear()
    await set_psycho(c.from_user.id, False)
    await c.message.edit_text("👋 Вышел из режима психолога")
    await c.answer()

@router.message(PsychoState.active, F.text != "🗣 Высказаться")
async def psycho_chat(m: Message):
    try:
        await m.chat.action("typing")
        
        user = await get_user(m.from_user.id)
        user_name = user.get("username") if user else None
        user_role = user.get("role", "user") if user else "user"
        
        # Собираем контекст
        context = f"""Ты — эмпатичный семейный психолог-бот.
Пользователь: {user_role} ({user_name}).
Твоя задача:
1. Выслушать и поддержать
2. Задать 1 уточняющий вопрос если нужно
3. НЕ давай прямых советов 'сделай то-то'
4. Используй 'Я-сообщения' и валидацию чувств
5. Будь тёплым, но не навязчивым
6. Ответь на русском, кратко (2-3 предложения)

Сообщение пользователя: {m.text}"""
        
        response = await generate(
            prompt=m.text,
            system=context,
            task_type="psycho",
            user_name=user_name
        )
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔚 Выйти", callback_data="psycho_exit")]
        ])
        
        await m.answer(response, reply_markup=kb, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Psycho error: {e}")
        await m.answer(
            "💙 *Я тебя слышу*\n\n"
            "Иногда просто нужно выговориться. "
            "Я рядом и поддерживаю тебя.\n\n"
            "Если хочешь, расскажи ещё что-то.",
            parse_mode="Markdown"
        )

@router.message(F.text == "🗣 Высказаться")
async def exit_psycho(m: Message, state: FSMContext):
    await state.clear()
    await set_psycho(m.from_user.id, False)
    logger.info(f"🧠 Psycho OFF: {m.from_user.id}")
    await m.answer("👋 *Обычный режим*\n\nЕсли понадобишься поддержка — я всегда рядом. Просто нажми 🧠 Психолог", parse_mode="Markdown")