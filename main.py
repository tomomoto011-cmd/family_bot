# main.py
import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager

# FastAPI для health check
from fastapi import FastAPI
import uvicorn

# Aiogram
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.storage.memory import MemoryStorage

# Наши модули
from config import BOT_TOKEN, DATABASE_URL, GEMINI_API_KEY, ADMIN_CHAT_ID, logger
from database import connect, create_tables, create_user, get_pool
from handlers import keyboards, psycho_router, challenges_router, family_router

# === FASTAPI LIFESPAN ===
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Инициализация при старте"""
    logger.info("🔄 Инициализация...")
    await connect()
    await create_tables()
    logger.info("✅ БД подключена")
    yield
    """Очистка при остановке"""
    logger.info("🛑 Завершение работы...")
    pool = await get_pool()
    if pool:
        await pool.close()

# === FASTAPI APP ===
app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def health_check():
    """Health check для Render/Railway"""
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return {"status": "healthy", "bot": "running", "db": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}

@app.get("/")
async def root():
    return {"message": "FamilyBot is running 🤖"}

# === AIOGRAM SETUP ===
storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)

# Подключаем ВСЕ роутеры
dp.include_router(psycho_router)
dp.include_router(challenges_router)
dp.include_router(family_router)

# === ОБЩИЕ ХЕНДЛЕРЫ ===

@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Команда /start"""
    try:
        await create_user(message.from_user.id, message.from_user.username)
        await message.answer(
            f"👋 *Добро пожаловать, {message.from_user.first_name}!*\n\n"
            "Я — семейный бот-помощник.\n"
            "Выбери роль, чтобы начать:",
            reply_markup=keyboards.role_keyboard(),
            parse_mode="Markdown"
        )
        logger.info(f"✅ Новый пользователь: {message.from_user.id}")
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
    help_text = (
        "📖 *Помощь*\n\n"
        "*Команды:*\n"
        "/start — начать работу\n"
        "/menu — показать меню\n"
        "/help — эта справка\n\n"
        "*Функции:*\n"
        "🧠 Психолог — поддержка и эмпатия\n"
        "🎯 Челлендж — задания и очки\n"
        "👨‍👩‍👧 Семья — управление семьёй\n"
        "💰 Баланс — твои очки и уровень\n"
        "🐶 Питомцы — семейные питомцы"
    )
    await message.answer(help_text, parse_mode="Markdown")

# === ОБРАБОТКА ВЫБОРА РОЛИ ===

@dp.message(F.text.in_({"Родитель", "Ребёнок", "Друг семьи"}))
async def set_role_handler(message: Message):
    """Установка роли пользователя"""
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
        logger.info(f"✅ Роль {role_code} установлена для {message.from_user.id}")
        
    except Exception as e:
        logger.error(f"Set role error: {e}")
        await message.answer("⚠️ Произошла ошибка. Попробуй позже")

# === ЗАПУСК: ПОЛЛИНГ + FASTAPI ===

async def start_polling_task():
    """Задача для запуска aiogram polling"""
    logger.info("🤖 Запуск aiogram polling...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.critical(f"💥 Polling crashed: {e}")
        raise

async def start_web_task():
    """Задача для запуска uvicorn server"""
    port = int(os.environ.get("PORT", 8000))
    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    logger.info(f"🌐 Запуск health server на порту {port}")
    await server.serve()

async def main():
    """Точка входа: запускаем оба сервера параллельно"""
    # Отправляем алерт админу
    if ADMIN_CHAT_ID:
        try:
            await bot.send_message(ADMIN_CHAT_ID, "✅ FamilyBot запустился!")
        except:
            pass
    
    # Запускаем polling и web server параллельно
    await asyncio.gather(
        start_polling_task(),
        start_web_task()
    )

if __name__ == "__main__":
    logger.info("🚀 FamilyBot v1.0 starting...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Остановка по сигналу")
    except Exception as e:
        logger.critical(f"💥 FATAL: {e}")
        sys.exit(1)