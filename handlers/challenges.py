from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from config import logger
from database import get_user, get_random_challenge, assign_challenge, complete_challenge, get_balance, add_points

router = Router()

@router.message(F.text == "🎯 Челлендж")
async def get_challenge(m: Message):
    try:
        user = await get_user(m.from_user.id)
        
        if not user or not user.get("role"):
            await m.answer(
                "⚠️ *Сначала выбери роль!*\n\n"
                "Напиши: `Родитель`, `Ребёнок` или `Друг семьи`",
                parse_mode="Markdown"
            )
            return
        
        challenge = await get_random_challenge(user["role"])
        
        if not challenge:
            await m.answer(
                "😢 *Пока нет челленджей*\n\n"
                "Попробуй позже или попроси родителя добавить новые задания",
                parse_mode="Markdown"
            )
            return
        
        # Проверяем, не выполнял ли уже сегодня
        from database import pool
        async with pool.acquire() as conn:
            exists = await conn.fetchval(
                """SELECT id FROM user_challenges 
                   WHERE user_id=$1 AND challenge_id=$2 AND DATE(created_at) = CURRENT_DATE""",
                m.from_user.id, challenge["id"]
            )
        
        if exists:
            await m.answer("✅ Ты уже выполнял этот челлендж сегодня! Отдохни 🌟")
            return
        
        await assign_challenge(m.from_user.id, challenge["id"])
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Выполнено", callback_data=f"challenge_done:{challenge['id']}")],
            [InlineKeyboardButton(text="❌ Пропустить", callback_data=f"challenge_skip:{challenge['id']}")]
        ])
        
        await m.answer(
            f"🎯 *Твой челлендж:*\n\n"
            f"{challenge['text']}\n\n"
            f"🏆 *Награда:* {challenge['reward']} очков\n\n"
            f"Когда выполнишь — нажми ✅",
            reply_markup=kb,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Challenge error: {e}")
        await m.answer("⚠️ Произошла ошибка. Попробуй позже")

@router.callback_query(F.data.startswith("challenge_done:"))
async def complete_challenge_cb(c: CallbackQuery):
    try:
        challenge_id = int(c.data.split(":")[1])
        reward = await complete_challenge(c.from_user.id)
        
        if reward:
            # Получаем новый баланс
            new_balance = await get_balance(c.from_user.id)
            
            # Определяем уровень
            if new_balance < 50:
                level = "🌱 Новичок"
            elif new_balance < 150:
                level = "🔥 Активист"
            else:
                level = "🏆 Лидер"
            
            await c.message.edit_text(
                f"🎉 *Отличная работа!*\n\n"
                f"+{reward} очков 🔥\n"
                f"Всего очков: {new_balance}\n"
                f"Уровень: {level}\n\n"
                f"Так держать! 💪",
                parse_mode="Markdown"
            )
            await c.answer("✅ Челлендж завершён!")
        else:
            await c.answer("⚠️ Уже завершён", show_alert=True)
            
    except Exception as e:
        logger.error(f"Complete callback error: {e}")
        await c.answer("⚠️ Ошибка", show_alert=True)

@router.callback_query(F.data.startswith("challenge_skip:"))
async def skip_challenge_cb(c: CallbackQuery):
    try:
        await c.message.edit_text(
            "⏭️ *Челлендж пропущен*\n\n"
            "Ничего страшного! Попробуй новый 🎯",
            parse_mode="Markdown"
        )
        await c.answer("Челлендж пропущен")
    except Exception as e:
        logger.error(f"Skip error: {e}")
        await c.answer("⚠️ Ошибка", show_alert=True)

@router.message(F.text.lower() == "готово")
async def complete_challenge_text(m: Message):
    try:
        reward = await complete_challenge(m.from_user.id)
        if reward:
            await m.answer(f"🎉 *Отлично!* +{reward} очков 🔥", parse_mode="Markdown")
        else:
            await m.answer("⚠️ Нет активного челленджа. Нажми 🎯 Челлендж", parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Complete text error: {e}")
        await m.answer("⚠️ Ошибка")

@router.message(F.text == "💰 Баланс")
async def show_balance(m: Message):
    try:
        points = await get_balance(m.from_user.id)
        
        # Определяем уровень
        if points < 50:
            level = "🌱 Новичок"
            next_level = "🔥 Активист (50 очков)"
        elif points < 150:
            level = "🔥 Активист"
            next_level = "🏆 Лидер (150 очков)"
        else:
            level = "🏆 Лидер"
            next_level = " Легенда (300 очков)"
        
        await m.answer(
            f"💰 *Твой баланс*\n\n"
            f"Очки: **{points}**\n"
            f"Уровень: {level}\n"
            f"Следующий: {next_level}\n\n"
            f"Продолжай выполнять челленджи!",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Balance error: {e}")
        await m.answer("⚠️ Произошла ошибка. Попробуй позже")

@router.message(F.text == "🎁 Дать очки")
async def give_points_prompt(m: Message):
    user = await get_user(m.from_user.id)
    if user.get("role") != "parent":
        await m.answer("🔒 Эта команда доступна только родителям")
        return
    
    await m.answer(
        "🎁 *Начисление очков*\n\n"
        "Формат: `Дать очки [число]`\n"
        "Пример: `Дать очки 10`\n\n"
        "⚠️ Доступно только родителям",
        parse_mode="Markdown"
    )

@router.message(F.text.startswith("дать очки"))
async def give_points_handler(m: Message):
    try:
        user = await get_user(m.from_user.id)
        if user.get("role") != "parent":
            await m.answer("🔒 Только для родителей")
            return
        
        parts = m.text.split()
        if len(parts) != 3:
            await m.answer("❌ Формат: `Дать очки 10`")
            return
        
        try:
            amount = int(parts[2])
            if amount < 0 or amount > 1000:
                await m.answer("❌ Сумма должна быть от 0 до 1000")
                return
            
            await add_points(m.from_user.id, amount)
            new_bal = await get_balance(m.from_user.id)
            await m.answer(f"✅ +{amount} очков начислено!\nНовый баланс: {new_bal}")
            logger.info(f"💰 {amount} points to {m.from_user.id}")
            
        except ValueError:
            await m.answer("❌ Укажи число, например: `Дать очки 10`")
            
    except Exception as e:
        logger.error(f"Give points error: {e}")
        await m.answer("⚠️ Ошибка")