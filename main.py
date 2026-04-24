import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from config import BOT_TOKEN, ADMIN_CHAT_ID, logger
from database import connect, create_tables, create_user
from handlers import keyboards, psycho, challenges, family

# Создаём бота и диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Подключаем роутеры
dp.include_router(psycho.router)
dp.include_router(challenges.router)
dp.include_router(family.router)

# === ОБЩИЕ ХЕНДЛЕРЫ ===

@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Команда /start"""
    try:
        await create_user(message.from_user.id, message.from_user.username)
        
        await message.answer(
            f"👋 *Добро пожаловать, {message.from_user.first_name}!*\n\n"
            "Я — семейный бот-помощник. "
            "Я помогу вам:\n"
            "• 🎯 Выполнять челленджи\n"
            "• 🧠 Получить поддержку\n"
            "• 👨‍👩‍👧 Объединиться в семью\n"
            "• 🏆 Соревноваться и зарабатывать очки\n\n"
            "Выбери роль, чтобы начать:\n"
            "• Родитель\n"
            "• Ребёнок\n"
            "• Друг семьи",
            reply_markup=keyboards.role_keyboard(),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Start error: {e}")
        await message.answer("⚠️ Произошла ошибка. Попробуй позже")

@dp.message(Command("menu"))
async def cmd_menu(message: Message):
    """Команда /menu"""
    await message.answer(
        "📋 *Главное меню*",
        reply_markup=keyboards.main_menu(),
        parse_mode="Markdown"
    )

@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Команда /help"""
    await message.answer(
        "📖 *Помощь*\n\n"
        "*Основные команды:*\n"
        "/start — начать работу\n"
        "/menu — показать меню\n"
        "/help — эта справка\n\n"
        "*Функции:*\n"
        "🧠 Психолог — поддержка\n"
        "🎯 Челлендж — задания\n"
        "👨‍‍👧 Семья — управление\n"
        "💰 Баланс — очки\n"
        "🐶 Питомцы — семейные питомцы",
        parse_mode="Markdown"
    )

# === ОБРАБОТКА РОЛИ ===

@dp.message(F.text.in_({"Родитель", "Ребёнок", "Друг семьи"}))
async def set_role_handler(message: Message):
    """Установка роли"""
    try:
        from database import set_role
        
        role_map = {
            "Родитель": "parent",
            "Ребёнок": "child",
            "Друг семьи": "friend"
        }
        
        role_text = message.text
        role_code = role_map[role_text]
        
        await set_role(message.from_user.id, role_code)
        
        await message.answer(
            f"✅ *Роль установлена: {role_text}*\n\n"
            "Теперь доступно главное меню!",
            reply_markup=keyboards.main_menu(),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Set role error: {e}")
        await message.answer("⚠️ Произошла ошибка. Попробуй позже")

# === ЗАПУСК ===

async def main():
    """Основная функция запуска"""
    try:
        # Подключение к БД
        await connect()
        await create_tables()
        
        logger.info("🤖 FamilyBot запускается...")
        
        # Отправляем уведомление админу
        if ADMIN_CHAT_ID:
            try:
                await bot.send_message(
                    ADMIN_CHAT_ID,
                    "✅ FamilyBot успешно запущен!"
                )
            except:
                pass
        
        # Запуск поллинга
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.critical(f"💥 Критическая ошибка: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())