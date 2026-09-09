import aiosqlite
import logging
from config import DB_NAME, SUPERADMIN_ID


# =====================================================================
# 1. ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ И ТАБЛИЦ
# =====================================================================

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("PRAGMA foreign_keys = ON;")

        # Таблица пользователей
        await db.execute("""
                         CREATE TABLE IF NOT EXISTS users
                         (
                             user_id
                             INTEGER
                             PRIMARY
                             KEY,
                             username
                             TEXT,
                             role
                             TEXT
                             DEFAULT
                             'user',
                             game
                             TEXT,
                             rank
                             TEXT,
                             hours
                             INTEGER,
                             prime_time
                             TEXT
                         )
                         """)

        # Автомиграция: добавляем колонки профиля, если база создавалась ранее
        cursor = await db.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in await cursor.fetchall()]
        for col, col_type in [('game', 'TEXT'), ('rank', 'TEXT'), ('hours', 'INTEGER'), ('prime_time', 'TEXT')]:
            if col not in columns:
                await db.execute(f"ALTER TABLE users ADD COLUMN {col} {col_type}")

        # Таблица лобби (заявок)
        await db.execute("""
                         CREATE TABLE IF NOT EXISTS orders
                         (
                             id
                             INTEGER
                             PRIMARY
                             KEY
                             AUTOINCREMENT,
                             user_id
                             INTEGER,
                             game
                             TEXT,
                             target_rank
                             TEXT,
                             slots
                             INTEGER,
                             description
                             TEXT,
                             status
                             TEXT
                             DEFAULT
                             'active',
                             FOREIGN
                             KEY
                         (
                             user_id
                         ) REFERENCES users
                         (
                             user_id
                         ) ON DELETE CASCADE
                             )
                         """)
        await db.commit()


# =====================================================================
# 2. РАБОТА С ПОЛЬЗОВАТЕЛЯМИ И РОЛЯМИ
# =====================================================================

async def get_or_create_user(user_id: int, username: str):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT role FROM users WHERE user_id = ?", (user_id,)) as cursor:
            user = await cursor.fetchone()
            if not user:
                role = 'admin' if user_id == SUPERADMIN_ID else 'user'
                await db.execute(
                    "INSERT INTO users (user_id, username, role) VALUES (?, ?, ?)",
                    (user_id, username or "Anonymous", role)
                )
                await db.commit()


async def get_user_role(user_id: int) -> str:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT role FROM users WHERE user_id = ?", (user_id,)) as cursor:
            res = await cursor.fetchone()
            return res[0] if res else 'user'


async def set_user_role(user_id: int, new_role: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET role = ? WHERE user_id = ?", (new_role, user_id))
        await db.commit()


# =====================================================================
# 3. РАБОТА С ПРОФИЛЕМ
# =====================================================================

async def get_user_profile(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
                "SELECT game, rank, hours, prime_time FROM users WHERE user_id = ?",
                (user_id,)
        ) as cursor:
            return await cursor.fetchone()


async def update_user_profile(user_id: int, game: str, rank: str, hours: int, prime_time: str,
                              username: str = "Anonymous"):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """INSERT INTO users (user_id, username, game, rank, hours, prime_time)
               VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT(user_id) DO
            UPDATE SET
                game = excluded.game,
                rank = excluded.rank,
                hours = excluded.hours,
                prime_time = excluded.prime_time""",
            (user_id, username, game, rank, hours, prime_time)
        )
        await db.commit()


async def delete_user_profile(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """UPDATE users
               SET game       = NULL,
                   rank       = NULL,
                   hours      = NULL,
                   prime_time = NULL
               WHERE user_id = ?""",
            (user_id,)
        )
        await db.commit()


# =====================================================================
# 4. РАБОТА С ЛОББИ (ORDERS)
# =====================================================================

async def create_order(user_id: int, game: str, target_rank: str, slots: int, description: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO orders (user_id, game, target_rank, slots, description) VALUES (?, ?, ?, ?, ?)",
            (user_id, game, target_rank, slots, description)
        )
        await db.commit()


# Возвращает active orders вместе с user_id создателя
async def get_active_orders():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("""
            SELECT orders.id, orders.game, orders.target_rank, orders.slots, orders.description, users.username, orders.user_id 
            FROM orders 
            JOIN users ON orders.user_id = users.user_id 
            WHERE orders.status = 'active'
            ORDER BY orders.id DESC
        """) as cursor:
            return await cursor.fetchall()

# Получение Telegram ID создателя конкретного лобби
async def get_order_owner(order_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT user_id FROM orders WHERE id = ?", (order_id,)) as cursor:
            res = await cursor.fetchone()
            return res[0] if res else None


async def close_order(order_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE orders SET status = 'closed' WHERE id = ?", (order_id,))
        await db.commit()