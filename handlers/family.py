# handlers/family.py
from aiogram import Router, F
from aiogram.types import Message
import random
import string
from config import logger
from database import get_user, create_family, join_family, get_pets, add_pet, get_family_stats, get_family_members, set_role

router = Router()

# 🔧 FIX: endswith вместо == (эмодзи в Telegram могут иметь разную кодировку)
@router.message(F.text.endswith("Семья"))
async def family_menu(m: Message):
    user = await get_user(m.from_user.id)
    
    if user and user.get("family_id"):
        members = await get_family_members(user["family_id"])
        
        member_list = "\n".join([
            f"• {mbr.get('username') or mbr.get('telegram_id')} — {mbr.get('role', 'участник')} ({mbr.get('points', 0)} очков)"
            for mbr in members
        ])
        
        await m.answer(
            f"👨‍‍👧 *Твоя семья*\n\n"
            f"Участники:\n{member_list}\n\n"
            f"Всего: {len(members)} человек\n\n"
            f"Команды:\n"
            f"• `/питомцы` — показать питомцев\n"
            f"• `/статистика` — рейтинг семьи\n"
            f"• `/меню` — главное меню",
            parse_mode="Markdown"
        )
    else:
        await m.answer(
            "👨‍👧 *Семья*\n\n"
            "Выбери действие:\n"
            "• `Создать семья [название]` — создать новую семью\n"
            "• `Войти [код]` — войти в существующую семью\n\n"
            "Пример: `Создать семья Ивановы`",
            parse_mode="Markdown"
        )

@router.message(F.text.startswith("Создать семья"))
async def create_family_handler(m: Message):
    try:
        name = m.text.replace("Создать семья ", "").strip()
        
        if len(name) < 2:
            await m.answer("⚠️ Название слишком короткое")
            return
        
        code = "FAM-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        family = await create_family(name, code)
        
        await m.answer(
            f"✅ *Семья создана!*\n\n"
            f"Название: **{name}**\n"
            f"🔑 Код для входа: `{code}`\n\n"
            "Теперь выбери свою роль:",
            parse_mode="Markdown"
        )
        
        from handlers.keyboards import role_keyboard
        await m.answer("Кто ты в семье?", reply_markup=role_keyboard())
        
        logger.info(f"👨‍👩‍👧 Family '{name}' created by {m.from_user.id}")
        
    except Exception as e:
        logger.error(f"Create family error: {e}")
        await m.answer("⚠️ Произошла ошибка. Попробуй позже")

@router.message(F.text.startswith("Войти"))
async def join_family_handler(m: Message):
    try:
        code = m.text.replace("Войти ", "").strip().upper()
        
        if not code:
            await m.answer("⚠️ Укажи код семьи")
            return
        
        family = await join_family(m.from_user.id, code)
        
        if family:
            await m.answer(
                f"✅ *Ты в семье!*\n\n"
                f"Семья: **{family['name']}**\n"
                f"Код: `{family['code']}`\n\n"
                "Теперь выбери свою роль:",
                parse_mode="Markdown"
            )
            
            from handlers.keyboards import role_keyboard
            await m.answer("Кто ты в семье?", reply_markup=role_keyboard())
            
            logger.info(f"👨‍👧 User {m.from_user.id} joined family {family['id']}")
        else:
            await m.answer(
                "❌ *Семья не найдена*\n\n"
                "Проверь код и попробуй снова",
                parse_mode="Markdown"
            )
            
    except Exception as e:
        logger.error(f"Join family error: {e}")
        await m.answer("⚠️ Произошла ошибка. Попробуй позже")

# 🔧 FIX: endswith вместо ==
@router.message(F.text.endswith("Питомцы"))
async def pets_handler(m: Message):
    try:
        user = await get_user(m.from_user.id)
        
        if not user or not user.get("family_id"):
            await m.answer(
                "⚠️ *Сначала вступи в семью!*\n"
                "Нажми 👨‍👩‍👧 Семья",
                parse_mode="Markdown"
            )
            return
        
        pets = await get_pets(user["family_id"])
        
        if pets:
            names = "\n".join([f"• {p['name']}" for p in pets])
            await m.answer(
                f"🐾 *Питомцы семьи*\n\n{names}",
                parse_mode="Markdown"
            )
        else:
            await m.answer(
                "🐾 *Нет питомцев*\n"
                "Напиши: `Добавить питомца [имя]`\n"
                "Пример: `Добавить питомца Бобик`",
                parse_mode="Markdown"
            )
            
    except Exception as e:
        logger.error(f"Pets error: {e}")
        await m.answer("⚠️ Произошла ошибка. Попробуй позже")

@router.message(F.text.startswith("Добавить питомца"))
async def add_pet_handler(m: Message):
    try:
        user = await get_user(m.from_user.id)
        
        if not user or not user.get("family_id"):
            await m.answer("⚠️ Сначала вступи в семью")
            return
        
        name = m.text.replace("Добавить питомца ", "").strip()
        
        if len(name) < 2:
            await m.answer("⚠️ Имя слишком короткое")
            return
        
        await add_pet(user["family_id"], name)
        
        await m.answer(f"✅ *{name}* добавлен в семью! 🐾", parse_mode="Markdown")
        logger.info(f"🐾 Pet '{name}' added to family {user['family_id']}")
        
    except Exception as e:
        logger.error(f"Add pet error: {e}")
        await m.answer("⚠️ Произошла ошибка. Попробуй позже")

# 🔧 FIX: endswith вместо ==
@router.message(F.text.endswith("Статистика"))
async def stats_handler(m: Message):
    try:
        user = await get_user(m.from_user.id)
        
        if not user or not user.get("family_id"):
            await m.answer("⚠️ Сначала вступи в семью")
            return
        
        stats = await get_family_stats(user["family_id"])
        
        if not stats:
            await m.answer("📊 Пока нет данных")
            return
        
        msg = "🏆 *Рейтинг семьи*\n\n"
        for i, s in enumerate(stats, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "•"
            username = s['username'] or f"User#{s['telegram_id']}"
            msg += f"{medal} {i}. {username} — {s['points']} очков\n"
        
        await m.answer(msg, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        await m.answer("⚠️ Произошла ошибка. Попробуй позже")