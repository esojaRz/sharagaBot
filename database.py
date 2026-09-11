from __future__ import annotations

import aiosqlite

from config import (
    ADMIN_TG_ID,
    DB_PATH,
    ROLE_ADMIN,
    ROLE_GAMER,
    STATUS_ARCHIVE,
    STATUS_COMPLETE,
    STATUS_RECRUITING,
)

SEED_GAMES = [
    ("Valorant", 5),
    ("CS2", 5),
    ("Dota 2", 5),
    ("League of Legends", 5),
    ("Apex Legends", 3),
    ("Rocket League", 3),
]


async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA foreign_keys = ON")
    return db


async def init_db() -> None:
    db = await get_db()
    try:
        await db.executescript(
            """
            CREATE TABLE IF NOT EXISTS user (
                id INTEGER PRIMARY KEY,
                nick TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'gamer',
                experience_years INTEGER NOT NULL DEFAULT 0,
                language TEXT NOT NULL DEFAULT 'ru',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                leader_id INTEGER NOT NULL,
                game TEXT NOT NULL,
                required_rank TEXT NOT NULL,
                free_slots INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'recruiting',
                platform TEXT NOT NULL,
                start_time TEXT NOT NULL,
                max_party INTEGER NOT NULL DEFAULT 5,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (leader_id) REFERENCES user(id)
            );

            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                max_party INTEGER NOT NULL DEFAULT 5
            );

            CREATE TABLE IF NOT EXISTS lobby_members (
                lobby_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                PRIMARY KEY (lobby_id, user_id),
                FOREIGN KEY (lobby_id) REFERENCES orders(id),
                FOREIGN KEY (user_id) REFERENCES user(id)
            );

            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lobby_id INTEGER,
                reporter_id INTEGER NOT NULL,
                reason TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (lobby_id) REFERENCES orders(id),
                FOREIGN KEY (reporter_id) REFERENCES user(id)
            );

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            """
        )
        for name, max_party in SEED_GAMES:
            await db.execute(
                "INSERT OR IGNORE INTO games (name, max_party) VALUES (?, ?)",
                (name, max_party),
            )
        await db.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES ('welcome_text', ?)",
            (
                "LFG: Game Matchmaker — ищем сквад без токсиков. "
                "Создай лобби или откликнись на чужой сбор.",
            ),
        )
        await db.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES ('prime_hint', '19:00-23:00')",
        )
        await db.commit()
    finally:
        await db.close()


async def get_user(tg_id: int) -> aiosqlite.Row | None:
    db = await get_db()
    try:
        cur = await db.execute("SELECT * FROM user WHERE id = ?", (tg_id,))
        return await cur.fetchone()
    finally:
        await db.close()


async def create_user(tg_id: int, nick: str, experience: int, language: str) -> None:
    role = ROLE_ADMIN if ADMIN_TG_ID and tg_id == ADMIN_TG_ID else ROLE_GAMER
    db = await get_db()
    try:
        await db.execute(
            """
            INSERT INTO user (id, nick, role, experience_years, language)
            VALUES (?, ?, ?, ?, ?)
            """,
            (tg_id, nick, role, experience, language),
        )
        await db.commit()
    finally:
        await db.close()


async def list_games() -> list[aiosqlite.Row]:
    db = await get_db()
    try:
        cur = await db.execute("SELECT * FROM games ORDER BY name")
        return await cur.fetchall()
    finally:
        await db.close()


async def get_game(name: str) -> aiosqlite.Row | None:
    db = await get_db()
    try:
        cur = await db.execute("SELECT * FROM games WHERE name = ?", (name,))
        return await cur.fetchone()
    finally:
        await db.close()


async def add_game(name: str, max_party: int) -> None:
    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO games (name, max_party) VALUES (?, ?)",
            (name, max_party),
        )
        await db.commit()
    finally:
        await db.close()


async def create_lobby(
    leader_id: int,
    game: str,
    platform: str,
    rank: str,
    start_time: str,
    free_slots: int,
    max_party: int,
) -> int:
    db = await get_db()
    try:
        cur = await db.execute(
            """
            INSERT INTO orders (
                leader_id, game, required_rank, free_slots, status,
                platform, start_time, max_party
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                leader_id,
                game,
                rank,
                free_slots,
                STATUS_RECRUITING,
                platform,
                start_time,
                max_party,
            ),
        )
        await db.commit()
        return cur.lastrowid
    finally:
        await db.close()


async def get_lobby(lobby_id: int) -> aiosqlite.Row | None:
    db = await get_db()
    try:
        cur = await db.execute(
            """
            SELECT o.*, u.nick AS leader_nick, u.language AS leader_lang
            FROM orders o
            JOIN user u ON u.id = o.leader_id
            WHERE o.id = ?
            """,
            (lobby_id,),
        )
        return await cur.fetchone()
    finally:
        await db.close()


async def list_open_lobbies() -> list[aiosqlite.Row]:
    db = await get_db()
    try:
        cur = await db.execute(
            """
            SELECT o.*, u.nick AS leader_nick
            FROM orders o
            JOIN user u ON u.id = o.leader_id
            WHERE o.status = ?
            ORDER BY o.id DESC
            LIMIT 20
            """,
            (STATUS_RECRUITING,),
        )
        return await cur.fetchall()
    finally:
        await db.close()


async def list_all_lobbies(limit: int = 30) -> list[aiosqlite.Row]:
    db = await get_db()
    try:
        cur = await db.execute(
            """
            SELECT o.*, u.nick AS leader_nick
            FROM orders o
            JOIN user u ON u.id = o.leader_id
            ORDER BY o.id DESC
            LIMIT ?
            """,
            (limit,),
        )
        return await cur.fetchall()
    finally:
        await db.close()


async def join_lobby(lobby_id: int, user_id: int) -> str:
    lobby = await get_lobby(lobby_id)
    if lobby is None:
        return "not_found"
    if lobby["status"] != STATUS_RECRUITING:
        return "closed"
    if lobby["leader_id"] == user_id:
        return "leader"
    if lobby["free_slots"] <= 0:
        return "full"

    db = await get_db()
    try:
        cur = await db.execute(
            "SELECT 1 FROM lobby_members WHERE lobby_id = ? AND user_id = ?",
            (lobby_id, user_id),
        )
        if await cur.fetchone():
            return "already"

        await db.execute(
            "INSERT INTO lobby_members (lobby_id, user_id, status) VALUES (?, ?, 'accepted')",
            (lobby_id, user_id),
        )
        new_slots = lobby["free_slots"] - 1
        status = STATUS_COMPLETE if new_slots == 0 else STATUS_RECRUITING
        await db.execute(
            "UPDATE orders SET free_slots = ?, status = ? WHERE id = ?",
            (new_slots, status, lobby_id),
        )
        await db.commit()
        return "complete" if status == STATUS_COMPLETE else "joined"
    finally:
        await db.close()


async def set_lobby_status(lobby_id: int, status: str) -> None:
    db = await get_db()
    try:
        await db.execute("UPDATE orders SET status = ? WHERE id = ?", (status, lobby_id))
        await db.commit()
    finally:
        await db.close()


async def archive_lobby(lobby_id: int) -> None:
    await set_lobby_status(lobby_id, STATUS_ARCHIVE)


async def complete_lobby(lobby_id: int) -> None:
    await set_lobby_status(lobby_id, STATUS_COMPLETE)


async def add_report(reporter_id: int, lobby_id: int | None, reason: str) -> None:
    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO reports (lobby_id, reporter_id, reason) VALUES (?, ?, ?)",
            (lobby_id, reporter_id, reason),
        )
        await db.commit()
    finally:
        await db.close()


async def list_open_reports() -> list[aiosqlite.Row]:
    db = await get_db()
    try:
        cur = await db.execute(
            """
            SELECT r.*, u.nick AS reporter_nick
            FROM reports r
            JOIN user u ON u.id = r.reporter_id
            WHERE r.status = 'open'
            ORDER BY r.id DESC
            """
        )
        return await cur.fetchall()
    finally:
        await db.close()


async def close_report(report_id: int) -> None:
    db = await get_db()
    try:
        await db.execute("UPDATE reports SET status = 'closed' WHERE id = ?", (report_id,))
        await db.commit()
    finally:
        await db.close()


async def set_user_role(user_id: int, role: str) -> bool:
    db = await get_db()
    try:
        cur = await db.execute("UPDATE user SET role = ? WHERE id = ?", (role, user_id))
        await db.commit()
        return cur.rowcount > 0
    finally:
        await db.close()


async def get_setting(key: str) -> str:
    db = await get_db()
    try:
        cur = await db.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = await cur.fetchone()
        return row["value"] if row else ""
    finally:
        await db.close()


async def set_setting(key: str, value: str) -> None:
    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
        await db.commit()
    finally:
        await db.close()
