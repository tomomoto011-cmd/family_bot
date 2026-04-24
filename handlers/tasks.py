from aiogram import Router
from aiogram.types import Message

from database import get_user, pool

router = Router()


def register(dp):
    dp.include_router(router)


@router.message(lambda message: message.text == "🎯 Челлендж")
async def get_challenge(message: Message):
    tg_id = message.from_user.id

    user = await get_user(tg_id)

    if not user or not user["role"]:
        await message.answer("Сначала выбери роль 👇")
        return

    async with pool.acquire() as conn:
        challenge = await conn.fetchrow(
            "SELECT * FROM challenges WHERE role=$1 ORDER BY RANDOM() LIMIT 1",
            user["role"]
        )

    if not challenge:
        await message.answer("Нет челленджей 😢")
        return

    await message.answer(
        f"🎯 Твой челлендж:\n\n{challenge['text']}\n\n🏆 Награда: {challenge['reward']} очков"
    )