from aiogram import Router, F
from aiogram.types import Message
from config import logger
from database import get_user, get_random_challenge, assign_challenge, complete_challenge, get_balance

router = Router()

@router.message(F.text == "🎯 Челлендж")
async def get_challenge(m: Message):
    try:
        u = await get_user(m.from_user.id)
        if not u or not u.get("role"): return await m.answer("⚠️ Сначала выбери роль: Родитель / Ребёнок / Друг семьи")
        ch = await get_random_challenge(u["role"])
        if not ch: return await m.answer("😢 Пока нет челленджей.")
        await assign_challenge(m.from_user.id, ch["id"])
        await m.answer(f"🎯 *Задание:*\n{ch['text']}\n\n🏆 Награда: {ch['reward']} очков\n_Напиши «Готово» когда выполнишь._", parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Chal err: {e}"); await m.answer("⚠️ Ошибка.")

@router.message(F.text.lower() == "готово")
async def complete_handler(m: Message):
    try:
        rw = await complete_challenge(m.from_user.id)
        await m.answer(f"🎉 Отлично! +{rw} очков 🔥" if rw else "⚠️ Нет активного челленджа.")
    except Exception as e:
        logger.error(f"Comp err: {e}"); await m.answer("⚠️ Ошибка.")

@router.message(F.text == "💰 Баланс")
async def show_balance(m: Message):
    try:
        pts = await get_balance(m.from_user.id)
        lvl = "🌱 Новичок" if pts < 50 else "🔥 Активист" if pts < 150 else "🏆 Лидер"
        await m.answer(f"💰 *Баланс*\nОчки: {pts}\nУровень: {lvl}", parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Bal err: {e}"); await m.answer("⚠️ Ошибка.")