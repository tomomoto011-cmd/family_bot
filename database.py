import asyncpg
import os
import random

DATABASE_URL = os.getenv("DATABASE_URL")

pool = None


async def connect():
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL)


async def create_tables():
    async with pool.acquire() as conn:
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            telegram_id BIGINT UNIQUE,
            role TEXT,
            family_id INT,
            points INT DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS families (
            id SERIAL PRIMARY KEY,
            name TEXT,
            code TEXT
        );

        CREATE TABLE IF NOT EXISTS challenges (
            id SERIAL PRIMARY KEY,
            text TEXT,
            reward INT,
            role TEXT
        );

        CREATE TABLE IF NOT EXISTS user_challenges (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            challenge_id INT,
            completed BOOLEAN DEFAULT FALSE
        );

        CREATE TABLE IF NOT EXISTS pets (
            id SERIAL PRIMARY KEY,
            family_id INT,
            name TEXT
        );
        """)


async def create_user(tg_id):
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO users (telegram_id) VALUES ($1) ON CONFLICT DO NOTHING",
            tg_id
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


async def create_family(name, code):
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            "INSERT INTO families (name, code) VALUES ($1, $2) RETURNING id",
            name, code
        )


async def join_family(tg_id, code):
    async with pool.acquire() as conn:
        family = await conn.fetchrow(
            "SELECT * FROM families WHERE code=$1", code
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
            "SELECT * FROM users WHERE family_id=$1",
            family_id
        )


async def get_family_stats(family_id):
    async with pool.acquire() as conn:
        return await conn.fetch(
            "SELECT telegram_id, points FROM users WHERE family_id=$1 ORDER BY points DESC",
            family_id
        )


async def get_random_challenge(role):
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM challenges WHERE role=$1", role
        )
        return random.choice(rows) if rows else None


async def assign_challenge(user_id, challenge_id):
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO user_challenges (user_id, challenge_id) VALUES ($1, $2)",
            user_id, challenge_id
        )


async def complete_challenge(user_id):
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
        SELECT uc.id, c.reward
        FROM user_challenges uc
        JOIN challenges c ON uc.challenge_id = c.id
        WHERE uc.user_id=$1 AND uc.completed=FALSE
        LIMIT 1
        """, user_id)

        if not row:
            return None

        await conn.execute(
            "UPDATE user_challenges SET completed=TRUE WHERE id=$1",
            row["id"]
        )

        await add_points(user_id, row["reward"])
        return row["reward"]


async def add_pet(family_id, name):
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO pets (family_id, name) VALUES ($1, $2)",
            family_id, name
        )


async def get_pets(family_id):
    async with pool.acquire() as conn:
        return await conn.fetch(
            "SELECT * FROM pets WHERE family_id=$1", family_id
        )


async def get_active_challenges():
    async with pool.acquire() as conn:
        return await conn.fetch("""
        SELECT user_id FROM user_challenges
        WHERE completed=FALSE
        """)