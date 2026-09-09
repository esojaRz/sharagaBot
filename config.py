import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_NAME = os.getenv("DB_NAME", "lfg_matchmaker.db")

raw_admin_id = os.getenv("SUPERADMIN_ID", "0")
SUPERADMIN_ID = int(raw_admin_id) if raw_admin_id.isdigit() else 0

if not BOT_TOKEN:
    raise ValueError("⚠️ Ошибка: BOT_TOKEN не найден в файле .env!")