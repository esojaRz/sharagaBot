
import aiosqlite

DB_NAME = "matchmaker.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
                         CREATE TABLE IF NOT EXISTS users (
                                                              user_id INTEGER PRIMARY KEY,
                                                              username TEXT,
                                                              role TEXT DEFAULT 'user',
                                                              game TEXT,
                                                              rank TEXT,
                                                              hours INTEGER,
                                                              prime_time TEXT
                         )
                         """)
        await db.execute("""
                         CREATE TABLE IF NOT EXISTS orders (
                                                               id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                               user_id INTEGER,
                                                               game TEXT,
                                                               rank TEXT,
                                                               slots INTEGER,
                                                               description TEXT,
                                                               status TEXT DEFAULT 'active'
                         )
                         """)
        await db.commit()

async def get_or_create_user(user_id: int, username: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
                         INSERT INTO users (user_id, username, role)
                         VALUES (?, ?, 'user')
                             ON CONFLICT(user_id) DO UPDATE SET username = excluded.username
                         """, (user_id, username))
        await db.commit()

async def get_user_role(user_id: int) -> str:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT role FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else "user"

async def get_user_profile(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT game, rank, hours, prime_time FROM users WHERE user_id = ?", (user_id,)) as cursor:
            return await cursor.fetchone()

async def update_user_profile(user_id: int, game: str, rank: str, hours: int, prime_time: str, username: str):
    async with aiosqlite.connect(DB_NAME) as db:
        # UPSERT: создаёт запись, если её не было, или обновляет существующую
        await db.execute("""
                         INSERT INTO users (user_id, username, game, rank, hours, prime_time)
                         VALUES (?, ?, ?, ?, ?, ?)
                             ON CONFLICT(user_id) DO UPDATE SET
                             username = excluded.username,
                                                         game = excluded.game,
                                                         rank = excluded.rank,
                                                         hours = excluded.hours,
                                                         prime_time = excluded.prime_time
                         """, (user_id, username, game, rank, hours, prime_time))
        await db.commit()

async def delete_user_profile(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE users SET game = NULL, rank = NULL, hours = NULL, prime_time = NULL WHERE user_id = ?",
            (user_id,)
        )
        await db.commit()

async def create_order(user_id: int, game: str, rank: str, slots: int, description: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO orders (user_id, game, rank, slots, description) VALUES (?, ?, ?, ?, ?)",
            (user_id, game, rank, slots, description)
        )
        await db.commit()

async def get_active_games():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT DISTINCT game FROM orders WHERE status = 'active'") as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

async def get_active_orders(game_filter: str = None):
    async with aiosqlite.connect(DB_NAME) as db:
        if game_filter:
            query = """
                    SELECT o.id, o.game, o.rank, o.slots, o.description, u.username, o.user_id
                    FROM orders o
                             JOIN users u ON o.user_id = u.user_id
                    WHERE o.status = 'active' AND LOWER(o.game) = LOWER(?)
                    ORDER BY o.id DESC \
                    """
            params = (game_filter,)
        else:
            query = """
                    SELECT o.id, o.game, o.rank, o.slots, o.description, u.username, o.user_id
                    FROM orders o
                             JOIN users u ON o.user_id = u.user_id
                    WHERE o.status = 'active'
                    ORDER BY o.id DESC \
                    """
            params = ()

        async with db.execute(query, params) as cursor:
            return await cursor.fetchall()

async def get_order_owner(lobby_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT user_id FROM orders WHERE id = ?", (lobby_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def close_order(lobby_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE orders SET status = 'closed' WHERE id = ?", (lobby_id,))
        await db.commit()


async def get_players(
        game_filter: str = None,
        min_hours: int = None,
        max_hours: int = None,
        prime_time_filter: str = None
):
    async with aiosqlite.connect(DB_NAME) as db:
        conditions = ["game IS NOT NULL", "game != ''"]
        params = []

        # Фильтр по игре
        if game_filter and game_filter != "all":
            conditions.append("LOWER(game) = LOWER(?)")
            params.append(game_filter)

        # Фильтр по часам (от и до)
        if min_hours is not None:
            conditions.append("hours >= ?")
            params.append(min_hours)

        if max_hours is not None:
            conditions.append("hours <= ?")
            params.append(max_hours)

        # Фильтр по прайм-тайму
        if prime_time_filter and prime_time_filter != "all":
            conditions.append("LOWER(prime_time) LIKE LOWER(?)")
            params.append(f"%{prime_time_filter}%")

        where_clause = " WHERE " + " AND ".join(conditions)
        query = f"""
            SELECT user_id, username, game, rank, hours, prime_time 
            FROM users 
            {where_clause}
            ORDER BY user_id DESC
        """

        async with db.execute(query, tuple(params)) as cursor:
            return await cursor.fetchall()

async def get_player_games():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT DISTINCT game FROM users WHERE game IS NOT NULL AND game != ''") as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]