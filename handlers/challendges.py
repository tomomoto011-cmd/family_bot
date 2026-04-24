# handlers/challenges.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from config import logger
from database import (
    get_user, get_random_challenge, assign_challenge, 
    complete_challenge, get_balance, add_points
)

router = Router()

@router.message(F.text == "🎯 Челлендж")
async def get_challenge(message: Message):
    """Получение случайного челленджа"""
    try:
        user = await get_user(message.from_user.id)
        
        if not user or not user.get("role"):
            await message.answer(
                "⚠️ *Сначала выбери роль!*\n\n"
                "Напиши: `Родитель`, `Ребёнок` или `Друг семьи`",
                parse_mode="Markdown"
            )
            return
        
        challenge = await get_random_challenge(user["role"])
        
        if not challenge:
            await message.answer(
                "😢 *Пока нет челленджей*\n\n"
                "Попробуй позже или попроси родителя добавить новые задания",
                parse_mode="Markdown"
            )
            return
        
        # Назначаем челлендж пользователю
        await assign_challenge(message.from_user.id, challenge["id"])
        
        # Формируем кнопки
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Выполнено", callback_data=f"challenge_done:{challenge['id']}")],
            [InlineKeyboardButton(text="❌ Пропустить", callback_data=f"challenge_skip:{challenge['id']}")]
        ])
        
        await message.answer(
            f"🎯 *Твой челлендж:*\n\n"
            f"{challenge['text']}\n\n"
            f"🏆 *Награда:* {challenge['reward']} очков\n\n"
            f"Когда выполнишь — нажми ✅",
            reply_markup=kb,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Challenge error: {e}")
        await message.answer("⚠️ Произошла ошибка. Попробуй позже")

@router.callback_query(F.data.startswith("challenge_done:"))
async def complete_challenge_callback(callback: CallbackQuery):
    """Завершение челленджа через кнопку"""
    try:
        challenge_id = int(callback.data.split(":")[1])
        reward = await complete_challenge(callback.from_user.id)
        
        if reward:
            await callback.message.edit_text(
                f"🎉 *Отличная работа!*\n\n"
                f"+{reward} очков 🔥\n"
                f"Так держать!",
                parse_mode="Markdown"
            )
            await callback.answer("✅ Челлендж завершён!")
        else:
            await callback.answer("⚠️ Челлендж уже завершён", show_alert=True)
            
    except Exception as e:
        logger.error(f"Complete challenge callback error: {e}")
        await callback.answer("⚠️ Ошибка", show_alert=True)

@router.callback_query(F.data.startswith("challenge_skip:"))
async def skip_challenge_callback(callback: CallbackQuery):
    """Пропуск челленджа"""
    try:
        # Просто удаляем активный челлендж без начисления очков
        await callback.message.edit_text(
            "⏭️ *Челлендж пропущен*\n\n"
            "Ничего страшного! Попробуй новый 🎯",
            parse_mode="Markdown"
        )
        await callback.answer("Челлендж пропущен")
        
    except Exception as e:
        logger.error(f"Skip challenge error: {e}")
        await callback.answer("⚠️ Ошибка", show_alert=True)

@router.message(F.text.lower() == "готово")
async def complete_challenge_text(message: Message):
    """Завершение челленджа текстовой командой"""
    try:
        reward = await complete_challenge(message.from_user.id)
        
        if reward:
            await message.answer(
                f"🎉 *Отличная работа!*\n\n"
                f"+{reward} очков 🔥\n"
                f"Так держать!",
                parse_mode="Markdown"
            )
        else:
            await message.answer(
                "⚠️ *Нет активного челленджа*\n\n"
                "Нажми 🎯 Челлендж, чтобы получить новое задание",
                parse_mode="Markdown"
            )
            
    except Exception as e:
        logger.error(f"Complete challenge text error: {e}")
        await message.answer("⚠️ Произошла ошибка. Попробуй позже")

@router.message(F.text == "💰 Баланс")
async def show_balance(message: Message):
    """Показ баланса очков"""
    try:
        points = await get_balance(message.from_user.id)
        
        # Определяем уровень
        if points < 50:
            level = "🌱 Новичок"
        elif points < 150:
            level = "🔥 Активист"
        else:
            level = "🏆 Лидер"
        
        await message.answer(
            f"💰 *Твой баланс*\n\n"
            f"Очки: **{points}**\n"
            f"Уровень: {level}\n\n"
            f"Продолжай выполнять челленджи!",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Balance error: {e}")
        await message.answer("⚠️ Произошла ошибка. Попробуй позже")

@router.message(F.text == "🎁 Дать очки")
async def give_points_prompt(message: Message):
    """Подсказка по начислению очков"""
    await message.answer(
        "🎁 *Начисление очков*\n\n"
        "Формат: `Дать очки [число]`\n"
        "Пример: `Дать очки 10`\n\n"
        "⚠️ Доступно только родителям",
        parse_mode="Markdown"
    )

@router.message(F.text.startswith("дать очки"))
async def give_points_handler(message: Message):
    """Начисление очков (только для родителей)"""
    try:
        user = await get_user(message.from_user.id)
        if user.get("role") != "parent":
            await message.answer("🔒 Эта команда доступна только родителям")
            return
        
        parts = message.text.split()
        if len(parts) != 3:
            await message.answer("❌ Формат: `Дать очки 10`")
            return
        
        try:
            amount = int(parts[2])
            if amount < 0 or amount > 1000:
                await message.answer("❌ Сумма должна быть от 0 до 1000")
                return
            
            await add_points(message.from_user.id, amount)
            await message.answer(f"✅ +{amount} очков начислено!")
            logger.info(f"💰 {amount} points added to {message.from_user.id}")
            
        except ValueError:
            await message.answer("❌ Укажи число, например: `Дать очки 10`")
            
    except Exception as e:
        logger.error(f"Give points error: {e}")
        await message.answer("⚠️ Произошла ошибка. Попробуй позже")