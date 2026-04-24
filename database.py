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
    raise RuntimeError("❌ Не удалось подключиться к БД после 3 попыток")

async def get_pool():
    """Получение пула соединений"""
    if pool is None:
        await connect()
    return pool

async def create_tables():
    """Создание таблиц"""
    async with pool.acquire() as conn:
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
        );

        CREATE TABLE IF NOT EXISTS families (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            code TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS challenges (
            id SERIAL PRIMARY KEY,
            text TEXT NOT NULL,
            reward INT DEFAULT 10,
            role TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS user_challenges (
            id SERIAL PRIMARY KEY,
            user_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
            challenge_id INT REFERENCES challenges(id) ON DELETE CASCADE,
            completed BOOLEAN DEFAULT FALSE,
            completed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(user_id, challenge_id, DATE(created_at))
        );

        CREATE TABLE IF NOT EXISTS pets (
            id SERIAL PRIMARY KEY,
            family_id INT REFERENCES families(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS reminders (
            id SERIAL PRIMARY KEY,
            user_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
            text TEXT NOT NULL,
            scheduled_at TIMESTAMP,
            is_sent BOOLEAN DEFAULT FALSE
        );
        """)
        logger.info("✅ Таблицы созданы/проверены")

# === ФУНКЦИИ ПОЛЬЗОВАТЕЛЕЙ ===

async def create_user(tg_id, username=None):
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO users (telegram_id, username) 
               VALUES ($1, $2) 
               ON CONFLICT (telegram_id) DO UPDATE SET 
               last_active = NOW(), username = COALESCE($2, users.username)""",
            tg_id, username
        )

async def get_user(tg_id):
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            "SELECT * FROM users WHERE telegram_id=$1", tg_id
        )

async def set_role(tg_id, role):
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET role=$1 WHERE telegram_id=$2",
            role, tg_id
        )

async def add_points(tg_id, amount):
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET points = points + $1 WHERE telegram_id=$2",
            amount, tg_id
        )

async def get_balance(tg_id):
    async with pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT points FROM users WHERE telegram_id=$1", tg_id
        )
        return user["points"] if user else 0

async def set_psycho_mode(tg_id, active: bool):
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET psycho_mode_active=$1 WHERE telegram_id=$2",
            active, tg_id
        )

async def is_psycho_mode(tg_id):
    async with pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT psycho_mode_active FROM users WHERE telegram_id=$1", tg_id
        )
        return user["psycho_mode_active"] if user else False

# === СЕМЬИ ===

async def create_family(name, code=None):
    """Создание семьи с авто-генерацией кода"""
    if not code:
        code = "FAM-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            "INSERT INTO families (name, code) VALUES ($1, $2) RETURNING id, code",
            name, code
        )

async def join_family(tg_id, code):
    """Вход в семью по коду"""
    async with pool.acquire() as conn:
        family = await conn.fetchrow(
            "SELECT * FROM families WHERE code=$1", code.upper()
        )
        
        if not family:
            return None
        
        await conn.execute(
            "UPDATE users SET family_id=$1 WHERE telegram_id=$2",
            family["id"], tg_id
        )
        
        return family

async def get_family_members(family_id):
    async with pool.acquire() as conn:
        return await conn.fetch(
            "SELECT * FROM users WHERE family_id=$1 ORDER BY points DESC",
            family_id
        )

async def get_family_stats(family_id):
    async with pool.acquire() as conn:
        return await conn.fetch(
            """SELECT u.telegram_id, u.username, u.points, 
                      COUNT(uc.id) as challenges_completed
               FROM users u
               LEFT JOIN user_challenges uc ON u.telegram_id = uc.user_id AND uc.completed = TRUE
               WHERE u.family_id=$1
               GROUP BY u.telegram_id, u.username, u.points
               ORDER BY u.points DESC""",
            family_id
        )

# === ЧЕЛЛЕНДЖИ ===

async def get_random_challenge(role):
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM challenges WHERE role=$1 AND is_active=TRUE", role
        )
        return random.choice(rows) if rows else None

async def assign_challenge(user_id, challenge_id):
    async with pool.acquire() as conn:
        try:
            await conn.execute(
                """INSERT INTO user_challenges (user_id, challenge_id) 
                   VALUES ($1, $2)
                   ON CONFLICT (user_id, challenge_id, DATE(created_at)) DO NOTHING""",
                user_id, challenge_id
            )
            return True
        except:
            return False

async def complete_challenge(user_id):
    """Завершение челленджа и начисление очков"""
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
        SELECT uc.id, c.reward
        FROM user_challenges uc
        JOIN challenges c ON uc.challenge_id = c.id
        WHERE uc.user_id=$1 AND uc.completed=FALSE
        ORDER BY uc.created_at DESC
        LIMIT 1
        """, user_id)

        if not row:
            return None

        # Отмечаем как выполненное
        await conn.execute(
            """UPDATE user_challenges 
               SET completed=TRUE, completed_at=NOW() 
               WHERE id=$1""",
            row["id"]
        )

        # Начисляем очки
        await add_points(user_id, row["reward"])
        
        return row["reward"]

async def get_active_challenges():
    """Получение всех активных челленджей для напоминаний"""
    async with pool.acquire() as conn:
        return await conn.fetch("""
        SELECT DISTINCT u.telegram_id as user_id
        FROM user_challenges uc
        JOIN users u ON uc.user_id = u.telegram_id
        WHERE uc.completed=FALSE
        """)

# === ПИТОМЦЫ ===

async def add_pet(family_id, name):
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO pets (family_id, name) VALUES ($1, $2)",
            family_id, name
        )

async def get_pets(family_id):
    async with pool.acquire() as conn:
        return await conn.fetch(
            "SELECT * FROM pets WHERE family_id=$1 ORDER BY name",
            family_id
        )

# === НАПОМИНАНИЯ ===

async def add_reminder(tg_id, text, scheduled_at=None):
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO reminders (user_id, text, scheduled_at) 
               VALUES ($1, $2, $3)""",
            tg_id, text, scheduled_at
        )

async def get_pending_reminders():
    async with pool.acquire() as conn:
        return await conn.fetch("""
        SELECT r.*, u.telegram_id
        FROM reminders r
        JOIN users u ON r.user_id = u.telegram_id
        WHERE r.is_sent=FALSE AND (r.scheduled_at IS NULL OR r.scheduled_at <= NOW())
        """)

async def mark_reminder_sent(reminder_id):
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE reminders SET is_sent=TRUE WHERE id=$1",
            reminder_id
        )