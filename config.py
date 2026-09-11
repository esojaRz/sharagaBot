import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
load_dotenv(ROOT / ".env.example")

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
if BOT_TOKEN.startswith("123456") or "your-token" in BOT_TOKEN.lower():
    BOT_TOKEN = ""
ADMIN_TG_ID = int(os.getenv("ADMIN_TG_ID", "0") or 0)
DB_PATH = os.getenv("DB_PATH", "lfg.db")

ROLE_GAMER = "gamer"
ROLE_CURATOR = "curator"
ROLE_ADMIN = "admin"

STATUS_RECRUITING = "recruiting"
STATUS_COMPLETE = "complete"
STATUS_ARCHIVE = "archive"

ROLE_LABELS = {
    ROLE_GAMER: "Геймер",
    ROLE_CURATOR: "Куратор",
    ROLE_ADMIN: "Админ",
}

STATUS_LABELS = {
    STATUS_RECRUITING: "Сбор",
    STATUS_COMPLETE: "Скомплектовано",
    STATUS_ARCHIVE: "Архив",
}
