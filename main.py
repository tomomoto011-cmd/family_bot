import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import CommandStart

from handlers.keyboards import main_menu, role_keyboard
from database import *
from ai import ask_grok

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(BOT_TOKEN)
dp = Dispatcher()


# 🔔 НАПОМИНАНИЯ
async def reminder_loop():
    while True:
        await asyncio.sleep(3600)

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
@dp.message(CommandStart())
async def start(message: Message):
    await create_user(message.from_user.id)

    await message.answer(
        "Добро пожаловать 👨‍👩‍👧",
        reply_markup=main_menu()
    )


# 🔥 ГЛАВНЫЙ ХЕНДЛЕР
@dp.message()
async def handler(message: Message):
    text = message.text
    user_id = message.from_user.id

    await create_user(user_id)
    user = await get_user(user_id)

    # 🧠 ПСИХОЛОГ (включение режима)
    if text == "🧠 Психолог":
        await message.answer("Я рядом. Напиши что чувствуешь 💬")
        return

    # 🗣 ВЫСКАЗАТЬСЯ
    elif text == "🗣 Высказаться":
        await message.answer("Говори всё как есть. Я не буду перебивать.")
        return

    # 👨‍👩‍👧 СЕМЬЯ
    elif text == "👨‍👩‍👧 Семья":
        await message.answer(
            "Создать семья ИМЯ\nили\nВойти КОД"
        )
        return

    # 🎯 ЧЕЛЛЕНДЖ
    elif text == "🎯 Челлендж":
        if not user or not user["role"]:
            await message.answer("Сначала выбери роль", reply_markup=role_keyboard())
            return

        challenge = await get_random_challenge(user["role"])

        if not challenge:
            await message.answer("Пока нет челленджей")
            return

        await assign_challenge(user_id, challenge["id"])

        await message.answer(
            f"🎯 {challenge['text']}\n\n"
            f"Награда: {challenge['reward']} очков\n\n"
            "Напиши ГОТОВО"
        )
        return

    # ✅ завершение
    elif text.lower() == "готово":
        reward = await complete_challenge(user_id)

        if reward:
            await message.answer(f"🔥 +{reward} очков")
        else:
            await message.answer("Нет активного челленджа")
        return

    # 💰 БАЛАНС
    elif text == "💰 Баланс":
        points = await get_balance(user_id)
        await message.answer(f"У тебя {points} очков 💰")
        return

    # 🎁 ДАТЬ ОЧКИ
    elif text.startswith("Дать очки"):
        try:
            amount = int(text.split()[2])
            await add_points(user_id, amount)
            await message.answer(f"+{amount} очков начислено")
        except:
            await message.answer("Формат: Дать очки 10")
        return

    # 🐶 ПИТОМЦЫ
    elif text == "🐶 Питомцы":
        if user and user["family_id"]:
            await add_pet(user["family_id"], "Питомец")
            await message.answer("Питомец добавлен 🐾")
        else:
            await message.answer("Сначала вступи в семью")
        return

    # 📊 СТАТИСТИКА
    elif text == "📊 Статистика":
        if not user or not user["family_id"]:
            await message.answer("Сначала семья")
            return

        stats = await get_family_stats(user["family_id"])

        msg = "🏆 Рейтинг:\n"
        for i, s in enumerate(stats, 1):
            msg += f"{i}. {s['telegram_id']} — {s['points']} очков\n"

        await message.answer(msg)
        return

    # 👇 команды
    elif text.startswith("Создать семья"):
        name = text.replace("Создать семья ", "")
        code = name.lower()

        await create_family(name, code)
        await message.answer(f"Семья создана. Код: {code}")
        return

    elif text.startswith("Войти"):
        code = text.replace("Войти ", "")

        family = await join_family(user_id, code)

        if family:
            await message.answer("Ты в семье 👍\nВыбери роль", reply_markup=role_keyboard())
        else:
            await message.answer("Семья не найдена")
        return

    elif text in ["Родитель", "Ребёнок", "Друг семьи"]:
        await set_role(user_id, text.lower())
        await message.answer(f"Роль установлена: {text}")
        return

    # 🧠 AI — ТОЛЬКО если не нажата кнопка
    elif text and len(text) > 5:
        reply = await ask_grok(text)
        await message.answer(reply)
        return

    # fallback
    else:
        await message.answer("Не понял 🤔", reply_markup=main_menu())


async def main():
    await connect()
    await create_tables()

    asyncio.create_task(reminder_loop())

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())