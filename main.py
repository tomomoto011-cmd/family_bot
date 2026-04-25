# main.py — ЧИСТЫЙ POLLING, БЕЗ FASTAPI
import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage

# Конфиги
from config import BOT_TOKEN, ADMIN_CHAT_ID, logger

# БД
from database import connect, create_tables, create_user, set_role

# Хендлеры (прямые импорты)
from handlers.keyboards import main_menu, role_keyboard
from handlers.psycho import router as psycho_router
from handlers.challenges import router as challenges_router
from handlers.family import router as family_router

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    stream=sys.stdout
)

# Создаём бота и диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Подключаем роутеры
dp.include_router(psycho_router)
dp.include_router(challenges_router)
dp.include_router(family_router)

# === ОБЩИЕ ХЕНДЛЕРЫ ===

@dp.message(Command("start"))
async def cmd_start(message: Message):
    logger.info(f"📨 /start от {message.from_user.id}")
    try:
        await create_user(message.from_user.id, message.from_user.username)
        await message.answer(
            f"👋 *Привет, {message.from_user.first_name}!*\nВыбери роль:",
            reply_markup=role_keyboard(),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Start error: {e}")
        await message.answer("⚠️ Ошибка")

@dp.message(Command("menu"))
async def cmd_menu(message: Message):
    await message.answer("📋 *Меню*:", reply_markup=main_menu(), parse_mode="Markdown")

@dp.message(F.text.in_({"Родитель", "Ребёнок", "Друг семьи"}))
async def set_role_handler(message: Message):
    try:
        role_map = {"Родитель": "parent", "Ребёнок": "child", "Друг семьи": "friend"}
        await set_role(message.from_user.id, role_map[message.text])
        await message.answer(f"✅ Роль: {message.text}", reply_markup=main_menu())
    except Exception as e:
        logger.error(f"Role error: {e}")
        await message.answer("⚠️ Ошибка")

# === ОТЛАДКА: Ловим ВСЕ сообщения ===
@dp.message()
async def debug_catch_all(message: Message):
    logger.info(f"📨 Catch-all: '{message.text}' от {message.from_user.id}")

# === ЗАПУСК ===

async def main():
    try:
        logger.info("🔄 Подключение к БД...")
        await connect()
        await create_tables()
        logger.info("✅ БД готова")
        
        logger.info("🔄 Проверка токена бота...")
        me = await bot.get_me()
        logger.info(f"✅ Бот авторизован: @{me.username} (ID: {me.id})")
        
        if ADMIN_CHAT_ID:
            try:
                await bot.send_message(ADMIN_CHAT_ID, f"✅ @{me.username} запустился!")
            except:
                pass
        
        logger.info("🤖 === ЗАПУСК ПОЛЛИНГА ===")
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.critical(f"💥 FATAL ERROR: {e}", exc_info=True)
        raise
    finally:
        await bot.session.close()
        logger.info("🔚 Сессия закрыта")

if __name__ == "__main__":
    logger.info("🚀 FamilyBot starting (polling mode)...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Остановка")