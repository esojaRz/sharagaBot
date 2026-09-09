import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from database import init_db
from handlers import main_router


async def main():
    logging.basicConfig(level=logging.INFO)

    # Автоматическая инициализация таблиц SQLite
    await init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Подключение всех роутеров
    dp.include_router(main_router)

    print("🚀 LFG Matchmaker Bot запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())