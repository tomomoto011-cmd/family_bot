import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.types import Message

from handlers.keyboards import main_menu, role_keyboard
from database import *
from ai import ask_grok

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(BOT_TOKEN)
dp = Dispatcher()


# 🔔 НАПОМИНАНИЯ
async def reminder_loop():
    while True:
        await asyncio.sleep(3600)  # каждый час

        users = await get_active_challenges()

        for u in users:
            try:
                await bot.send_message(
                    u["user_id"],
                    "⏰ Напоминание: у тебя есть незавершённый челлендж"
                )
            except:
                pass


# 🚀 старт
@dp.message()
async def handler(message: Message):
    text = message.text.lower()
    user = await get_user(message.from_user.id)

    # 🧠 ПСИХО РЕЖИМ (через Grok)
    if text.startswith("психо"):
        reply = await ask_grok(text)
        await message.answer(reply)

    # 📊 СТАТИСТИКА
    elif text == "статистика":
        stats = await get_family_stats(user["family_id"])

        msg = "🏆 Рейтинг:\n"
        for i, s in enumerate(stats, 1):
            msg += f"{i}. {s['telegram_id']} — {s['points']} очков\n"

        await message.answer(msg)

    else:
        await message.answer("Работаю 👀", reply_markup=main_menu())


async def main():
    await connect()
    await create_tables()

    # запускаем напоминания
    asyncio.create_task(reminder_loop())

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())