# database.py
import asyncpg
import asyncio
import logging
import random
import string
from config import DATABASE_URL, logger

pool = None

async def connect():
    """Подключение к БД с retry"""
    global pool
    for attempt in range(3):
        try:
            pool = await asyncpg.create_pool(
                DATABASE_URL,
                min_size=2,
                max_size=10,
                command_timeout=30,
                ssl="require" if "neon" in DATABASE_URL else None
            )
            logger.info("✅ БД подключена успешно")
            return
        except Exception as e:
            logger.warning(f"⚠️ Попытка подключения {attempt+1}/3: {e}")
            await asyncio.sleep(2 * (attempt + 1))
    raise RuntimeError("❌ Не удалось подключиться к БД")

async def get_pool():
    if pool is None:
        await connect()
    return pool

async def create_tables():
    """Создание таблиц (чистый PostgreSQL)"""
    async with pool.acquire() as conn:
        # 1. Users
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL,
                username TEXT,
                role TEXT CHECK (role IN ('parent', 'teen', 'child', 'friend')),
                family_id INT REFERENCES families(id),
                points INT DEFAULT 0,
                psycho_mode_active BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW(),
                last_active TIMESTAMP DEFAULT NOW()
            )
        """)
        logger.info("✅ Таблица users готова")

        # 2. Families
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS families (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                code TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        logger.info("✅ Таблица families готова")

        # 3. Challenges
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS challenges (
                id SERIAL PRIMARY KEY,
                text TEXT NOT NULL,
                reward INT DEFAULT 10,
                role TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        logger.info("✅ Таблица challenges готова")

        # 4. User Challenges
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_challenges (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
                challenge_id INT REFERENCES challenges(id) ON DELETE CASCADE,
                completed BOOLEAN DEFAULT FALSE,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        # Индекс для предотвращения дублей за день
        await conn.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_user_challenge_daily 
            ON user_challenges (user_id, challenge_id, DATE(created_at))
        """)
        logger.info("✅ Таблица user_challenges готова")

        # 5. Pets
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS pets (
                id SERIAL PRIMARY KEY,
                family_id INT REFERENCES families(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        logger.info("✅ Таблица pets готова")

        # 6. Reminders
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
                text TEXT NOT NULL,
                scheduled_at TIMESTAMP,
                is_sent BOOLEAN DEFAULT FALSE
            )
        """)
        logger.info("✅ Таблица reminders готова")

# === ВСЕ ОСТАЛЬНЫЕ ФУНКЦИИ ОСТАВЬ КАК БЫЛИ ===
# (create_user, get_user, set_role, add_points, get_balance, set_psycho_mode, 
# is_psycho_mode, create_family, join_family, get_family_members, get_family_stats, 
# get_random_challenge, assign_challenge, complete_challenge, get_active_challenges, 
# add_pet, get_pets, add_reminder, get_pending_reminders, mark_reminder_sent)