
import asyncio
import aiosqlite
from aiogram import Bot
from config import BOT_TOKEN, DB_NAME

async def test_all():
    print("🔍 Начинаем проверку окружения...\n")

    # 1. Проверка подключения к SQLite
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("SELECT 1")
        print("✅ [База данных]: Успешное подключение к SQLite!")
    except Exception as e:
        print(f"❌ [База данных]: Ошибка подключения — {e}")
        return

    # 2. Проверка Telegram API и токена бота
    try:
        bot = Bot(token=BOT_TOKEN)
        bot_info = await bot.get_me()
        print(f"✅ [Telegram API]: Токен валиден! Бот: @{bot_info.username} (ID: {bot_info.id})")
        await bot.session.close()
    except Exception as e:
        print(f"❌ [Telegram API]: Ошибка подключения/неверный токен — {e}")
        return

    print("\n🎉 Все проверки пройдены! Можно запускать бота.")

if __name__ == "__main__":
    asyncio.run(test_all())