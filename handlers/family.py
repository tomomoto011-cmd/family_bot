from aiogram import Router, F
from aiogram.types import Message
from database import (
    get_user, create_family, join_family, 
    get_family_members, get_pets, add_pet
)
from config import logger

router = Router()

@router.message(F.text == "👨‍👩‍👧 Семья")
async def family_menu(message: Message):
    """Меню семьи"""
    user = await get_user(message.from_user.id)
    
    if user and user["family_id"]:
        await message.answer(
            "👨‍‍👧 *Твоя семья*\n\n"
            "Ты уже в семье! Доступные команды:\n\n"
            "• `/семья` — показать информацию\n"
            "• `/питомцы` — показать питомцев\n"
            "• `/статистика` — рейтинг семьи",
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            "👨‍‍👧 *Семья*\n\n"
            "Выбери действие:\n\n"
            "• `Создать семья [название]` — создать новую семью\n"
            "• `Войти [код]` — войти в существующую семью\n\n"
            "Пример: `Создать семья Ивановы`",
            parse_mode="Markdown"
        )

@router.message(F.text.startswith("Создать семья"))
async def create_family_handler(message: Message):
    """Создание семьи"""
    try:
        name = message.text.replace("Создать семья ", "").strip()
        
        if len(name) < 2:
            await message.answer("⚠️ Название слишком короткое")
            return
        
        family = await create_family(name)
        
        await message.answer(
            f"✅ *Семья создана!*\n\n"
            f"Название: **{name}**\n"
            f"Код для входа: `{family['code']}`\n\n"
            "Отправь этот код близким, чтобы они присоединились",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Create family error: {e}")
        await message.answer("⚠️ Произошла ошибка. Попробуй позже")

@router.message(F.text.startswith("Войти"))
async def join_family_handler(message: Message):
    """Вход в семью"""
    try:
        code = message.text.replace("Войти ", "").strip()
        
        if not code:
            await message.answer("⚠️ Укажи код семьи")
            return
        
        family = await join_family(message.from_user.id, code)
        
        if family:
            await message.answer(
                f"✅ *Ты в семье!*\n\n"
                f"Семья: **{family['name']}**\n"
                f"Код: `{family['code']}`\n\n"
                "Теперь ты можешь участвовать в семейных челленджах!",
                parse_mode="Markdown"
            )
        else:
            await message.answer(
                "❌ *Семья не найдена*\n\n"
                "Проверь код и попробуй снова",
                parse_mode="Markdown"
            )
            
    except Exception as e:
        logger.error(f"Join family error: {e}")
        await message.answer("⚠️ Произошла ошибка. Попробуй позже")

@router.message(F.text == "🐶 Питомцы")
async def pets_handler(message: Message):
    """Показ питомцев"""
    try:
        user = await get_user(message.from_user.id)
        
        if not user or not user["family_id"]:
            await message.answer(
                "⚠️ *Сначала вступи в семью!*\n\n"
                "Нажми 👨‍‍👧 Семья",
                parse_mode="Markdown"
            )
            return
        
        pets = await get_pets(user["family_id"])
        
        if pets:
            names = "\n".join([f"• {p['name']}" for p in pets])
            await message.answer(
                f"🐾 *Питомцы семьи*\n\n{names}",
                parse_mode="Markdown"
            )
        else:
            await message.answer(
                "🐾 *Нет питомцев*\n\n"
                "Напиши: `Добавить питомца [имя]`\n"
                "Пример: `Добавить питомца Бобик`",
                parse_mode="Markdown"
            )
            
    except Exception as e:
        logger.error(f"Pets error: {e}")
        await message.answer("⚠️ Произошла ошибка. Попробуй позже")

@router.message(F.text.startswith("Добавить питомца"))
async def add_pet_handler(message: Message):
    """Добавление питомца"""
    try:
        user = await get_user(message.from_user.id)
        
        if not user or not user["family_id"]:
            await message.answer("⚠️ Сначала вступи в семью")
            return
        
        name = message.text.replace("Добавить питомца ", "").strip()
        
        if len(name) < 2:
            await message.answer("⚠️ Имя слишком короткое")
            return
        
        await add_pet(user["family_id"], name)
        
        await message.answer(f"✅ *{name}* добавлен в семью! 🐾", parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Add pet error: {e}")
        await message.answer("⚠️ Произошла ошибка. Попробуй позже")

@router.message(F.text == "📊 Статистика")
async def stats_handler(message: Message):
    """Статистика семьи"""
    try:
        user = await get_user(message.from_user.id)
        
        if not user or not user["family_id"]:
            await message.answer("⚠️ Сначала вступи в семью")
            return
        
        stats = await get_family_stats(user["family_id"])
        
        if not stats:
            await message.answer("📊 Пока нет данных")
            return
        
        msg = "🏆 *Рейтинг семьи*\n\n"
        for i, s in enumerate(stats, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "•"
            msg += f"{medal} {i}. {s['username'] or s['telegram_id']} — {s['points']} очков\n"
        
        await message.answer(msg, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        await message.answer("⚠️ Произошла ошибка. Попробуй позже")