import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

import database as db
from config import BOT_TOKEN
from handlers import setup_routers


async def main() -> None:
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    if not BOT_TOKEN:
        raise SystemExit("Заполни BOT_TOKEN в файле .env (см. .env.example).")

    await db.init_db()
    bot = Bot(BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    setup_routers(dp)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
