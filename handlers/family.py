from aiogram import Router, F
from aiogram.types import Message
import random, string
from config import logger
from database import get_user, create_family, join_family, get_pets, add_pet, get_family_stats

router = Router()

@router.message(F.text == "👨‍👩‍👧 Семья")
async def family_menu(m: Message):
    u = await get_user(m.from_user.id)
    if u and u.get("family_id"):
        await m.answer("👨‍‍👧 Ты в семье!\n• `/питомцы` — показать питомцев\n• `/статистика` — рейтинг")
    else:
        await m.answer("👨‍‍👧 *Семья*\n• `Создать семья [название]`\n• `Войти [код]`\nПример: `Создать семья Ивановы`", parse_mode="Markdown")

@router.message(F.text.startswith("Создать семья"))
async def create_family_h(m: Message):
    try:
        name = m.text.replace("Создать семья ", "").strip()
        if len(name)<2: return await m.answer("⚠️ Короткое имя")
        code = "FAM-" + ''.join(random.choices(string.ascii_uppercase+string.digits, k=6))
        f = await create_family(name, code)
        await m.answer(f"✅ Семья создана!\n🔑 Код: `{code}`\nОтправь код близким.", parse_mode="Markdown")
    except Exception as e:
        logger.error(f"CF err: {e}"); await m.answer("⚠️ Ошибка.")

@router.message(F.text.startswith("Войти"))
async def join_family_h(m: Message):
    try:
        code = m.text.replace("Войти ", "").strip().upper()
        if not code: return await m.answer("⚠️ Укажи код")
        f = await join_family(m.from_user.id, code)
        await m.answer(f"✅ Ты в семье: {f['name']}" if f else "❌ Не найдена. Проверь код.")
    except Exception as e:
        logger.error(f"JF err: {e}"); await m.answer("⚠️ Ошибка.")

@router.message(F.text == "🐶 Питомцы")
async def pets_h(m: Message):
    try:
        u = await get_user(m.from_user.id)
        if not u or not u.get("family_id"): return await m.answer("⚠️ Сначала вступи в семью")
        pets = await get_pets(u["family_id"])
        await m.answer("🐾 Питомцы:\n"+"\n".join([f"• {p['name']}" for p in pets]) if pets else "🐾 Нет. Напиши: `Добавить питомца [имя]`", parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Pets err: {e}"); await m.answer("⚠️ Ошибка.")

@router.message(F.text.startswith("Добавить питомца"))
async def add_pet_h(m: Message):
    try:
        u = await get_user(m.from_user.id)
        if not u or not u.get("family_id"): return await m.answer("⚠️ Сначала вступи в семью")
        name = m.text.replace("Добавить питомца ", "").strip()
        if len(name)<2: return await m.answer("⚠️ Короткое имя")
        await add_pet(u["family_id"], name)
        await m.answer(f"✅ {name} добавлен! 🐾", parse_mode="Markdown")
    except Exception as e:
        logger.error(f"AP err: {e}"); await m.answer("⚠️ Ошибка.")

@router.message(F.text == "📊 Статистика")
async def stats_h(m: Message):
    try:
        u = await get_user(m.from_user.id)
        if not u or not u.get("family_id"): return await m.answer("⚠️ Сначала вступи в семью")
        stats = await get_family_stats(u["family_id"])
        if not stats: return await m.answer("📊 Пока нет данных")
        msg = "🏆 Рейтинг:\n"
        for i, s in enumerate(stats, 1):
            msg += f"{'🥇' if i==1 else '🥈' if i==2 else '🥉' if i==3 else '•'} {i}. {s['username'] or s['telegram_id']} — {s['points']} очков\n"
        await m.answer(msg, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Stats err: {e}"); await m.answer("⚠️ Ошибка.")