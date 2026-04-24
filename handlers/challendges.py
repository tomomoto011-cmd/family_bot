from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from database import (
    get_user, get_random_challenge, assign_challenge, 
    complete_challenge, get_balance
)
from config import logger

router = Router()

@router.message(F.text == "🎯 Челлендж")
async def get_challenge(message: Message):
    """Получение случайного челленджа"""
    try:
        user = await get_user(message.from_user.id)
        
        if not user or not user["role"]:
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
        
        await message.answer(
            f"🎯 *Твой челлендж:*\n\n"
            f"{challenge['text']}\n\n"
            f"🏆 *Награда:* {challenge['reward']} очков\n\n"
            f"Когда выполнишь — напиши **Готово** или нажми ✅",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Challenge error: {e}")
        await message.answer("⚠️ Произошла ошибка. Попробуй позже")

@router.message(F.text.lower() == "готово")
async def complete_challenge_handler(message: Message):
    """Завершение челленджа"""
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
        logger.error(f"Complete challenge error: {e}")
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