# main.py
import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, ADMIN_CHAT_ID, logger
from database import connect, create_tables, create_user, set_role
from handlers.keyboards import main_menu, role_keyboard
from handlers.psycho import router as psycho_r
from handlers.challenges import router as chal_r
from handlers.family import router as fam_r

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s", stream=sys.stdout)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# === РЕГИСТРАЦИЯ РОУТЕРОВ ===
dp.include_router(psycho_r)
dp.include_router(chal_r)
dp.include_router(fam_r)

# === ЛОГИРОВАНИЕ ВСЕХ СООБЩЕНИЙ ===
@dp.message()
async def log_all_messages(m: Message):
    logger.info(f"📨 [{m.from_user.username or m.from_user.id}]: '{m.text}'")

# === ОБЩИЕ ХЕНДЛЕРЫ ===

@dp.message(Command("start"))
async def cmd_start(m: Message):
    logger.info(f"📥 /start от {m.from_user.id}")
    await create_user(m.from_user.id, m.from_user.username)
    await m.answer(f"👋 *Привет, {m.from_user.first_name}!*\nВыбери роль:", reply_markup=role_keyboard(), parse_mode="Markdown")

@dp.message(Command("menu"))
async def cmd_menu(m: Message):
    logger.info(f"📥 /menu от {m.from_user.id}")
    await m.answer("📋 *Меню*:", reply_markup=main_menu(), parse_mode="Markdown")

@dp.message(F.text.in_({"Родитель", "Ребёнок", "Друг семьи"}))
async def set_role_h(m: Message):
    logger.info(f"📥 Роль: {m.text}")
    await set_role(m.from_user.id, {"Родитель":"parent","Ребёнок":"child","Друг семьи":"friend"}[m.text])
    await m.answer(f"✅ Роль: {m.text}", reply_markup=main_menu())

# === ЗАПУСК ===

async def main():
    try:
        logger.info("🔄 БД...")
        await connect()
        await create_tables()
        logger.info("✅ БД готова")
        
        logger.info("🔄 Токен...")
        me = await bot.get_me()
        logger.info(f"✅ Бот: @{me.username}")
        
        if ADMIN_CHAT_ID:
            try: 
                await bot.send_message(ADMIN_CHAT_ID, f"✅ @{me.username} запущен!")
            except: 
                pass
        
        logger.info("🤖 === ПОЛЛИНГ ===")
        await dp.start_polling(bot)
    except Exception as e:
        logger.critical(f"💥 {e}", exc_info=True)
        raise
    finally:
        await bot.session.close()

if __name__ == "__main__":
    logger.info("🚀 Старт...")
    asyncio.run(main())