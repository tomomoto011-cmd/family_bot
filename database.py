import asyncpg
import asyncio
import random
import string
from config import DATABASE_URL, logger

pool = None

async def connect():
    global pool
    for i in range(3):
        try:
            pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10, command_timeout=30, ssl="require" if "neon" in DATABASE_URL else None)
            logger.info("✅ БД подключена")
            return
        except Exception as e:
            logger.warning(f"⚠️ Попытка {i+1}/3: {e}")
            await asyncio.sleep(2)
    raise RuntimeError("❌ Нет подключения к БД")

async def get_pool():
    if pool is None: await connect()
    return pool

async def create_tables():
    async with pool.acquire() as conn:
        for sql in [
            """CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, telegram_id BIGINT UNIQUE, username TEXT, role TEXT CHECK(role IN('parent','teen','child','friend')), family_id INT REFERENCES families(id), points INT DEFAULT 0, psycho_active BOOLEAN DEFAULT FALSE, created_at TIMESTAMP DEFAULT NOW())""",
            """CREATE TABLE IF NOT EXISTS families (id SERIAL PRIMARY KEY, name TEXT NOT NULL, code TEXT UNIQUE NOT NULL, created_at TIMESTAMP DEFAULT NOW())""",
            """CREATE TABLE IF NOT EXISTS challenges (id SERIAL PRIMARY KEY, text TEXT NOT NULL, reward INT DEFAULT 10, role TEXT, is_active BOOLEAN DEFAULT TRUE, created_at TIMESTAMP DEFAULT NOW())""",
            """CREATE TABLE IF NOT EXISTS user_challenges (id SERIAL PRIMARY KEY, user_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE, challenge_id INT REFERENCES challenges(id) ON DELETE CASCADE, completed BOOLEAN DEFAULT FALSE, completed_at TIMESTAMP, created_at TIMESTAMP DEFAULT NOW())""",
            """CREATE UNIQUE INDEX IF NOT EXISTS idx_uc_daily ON user_challenges (user_id, challenge_id, DATE(created_at))""",
            """CREATE TABLE IF NOT EXISTS pets (id SERIAL PRIMARY KEY, family_id INT REFERENCES families(id) ON DELETE CASCADE, name TEXT NOT NULL, created_at TIMESTAMP DEFAULT NOW())""",
            """CREATE TABLE IF NOT EXISTS reminders (id SERIAL PRIMARY KEY, user_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE, text TEXT NOT NULL, scheduled_at TIMESTAMP, is_sent BOOLEAN DEFAULT FALSE)"""
        ]:
            await conn.execute(sql)
        logger.info("✅ Таблицы готовы")

# --- USERS ---
async def create_user(tg, uname=None):
    async with pool.acquire() as c: await c.execute("INSERT INTO users(telegram_id,username) VALUES($1,$2) ON CONFLICT(telegram_id) DO UPDATE SET username=COALESCE($2,users.username)", tg, uname)
async def get_user(tg):
    async with pool.acquire() as c: return await c.fetchrow("SELECT * FROM users WHERE telegram_id=$1", tg)
async def set_role(tg, role):
    async with pool.acquire() as c: await c.execute("UPDATE users SET role=$1 WHERE telegram_id=$2", role, tg)
async def add_points(tg, amt):
    async with pool.acquire() as c: await c.execute("UPDATE users SET points=points+$1 WHERE telegram_id=$2", amt, tg)
async def get_balance(tg):
    async with pool.acquire() as c:
        r = await c.fetchrow("SELECT points FROM users WHERE telegram_id=$1", tg)
        return r["points"] if r else 0
async def set_psycho(tg, val):
    async with pool.acquire() as c: await c.execute("UPDATE users SET psycho_active=$1 WHERE telegram_id=$2", val, tg)
async def is_psycho(tg):
    async with pool.acquire() as c:
        r = await c.fetchrow("SELECT psycho_active FROM users WHERE telegram_id=$1", tg)
        return bool(r["psycho_active"]) if r else False

# --- FAMILY ---
async def create_family(name, code=None):
    if not code: code = "FAM-" + ''.join(random.choices(string.ascii_uppercase+string.digits, k=6))
    async with pool.acquire() as c: return await c.fetchrow("INSERT INTO families(name,code) VALUES($1,$2) RETURNING id,code", name, code)
async def join_family(tg, code):
    async with pool.acquire() as c:
        f = await c.fetchrow("SELECT * FROM families WHERE code=$1", code.upper())
        if not f: return None
        await c.execute("UPDATE users SET family_id=$1 WHERE telegram_id=$2", f["id"], tg)
        return f
async def get_pets(fid):
    async with pool.acquire() as c: return await c.fetch("SELECT * FROM pets WHERE family_id=$1 ORDER BY name", fid)
async def add_pet(fid, name):
    async with pool.acquire() as c: await c.execute("INSERT INTO pets(family_id,name) VALUES($1,$2)", fid, name)
async def get_family_stats(fid):
    async with pool.acquire() as c: return await c.fetch("SELECT u.telegram_id, u.username, u.points FROM users u WHERE u.family_id=$1 ORDER BY u.points DESC", fid)

# --- CHALLENGES ---
async def get_random_challenge(role):
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM challenges WHERE role=$1 ORDER BY RANDOM() LIMIT 5", role)
        return random.choice(rows) if rows else None
async def assign_challenge(uid, cid):
    async with pool.acquire() as c:
        try: await c.execute("INSERT INTO user_challenges(user_id,challenge_id) VALUES($1,$2) ON CONFLICT(user_id,challenge_id,DATE(created_at)) DO NOTHING", uid, cid); return True
        except: return False
async def complete_challenge(uid):
    async with pool.acquire() as c:
        row = await c.fetchrow("SELECT uc.id, c.reward FROM user_challenges uc JOIN challenges c ON uc.challenge_id=c.id WHERE uc.user_id=$1 AND uc.completed=FALSE ORDER BY uc.created_at DESC LIMIT 1", uid)
        if not row: return None
        await c.execute("UPDATE user_challenges SET completed=TRUE, completed_at=NOW() WHERE id=$1", row["id"])
        await add_points(uid, row["reward"])
        return row["reward"]