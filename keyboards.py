from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def main_menu(role: str) -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text="➕ Создать лобби")
    kb.button(text="🌐 Открытые лобби")
    kb.button(text="👤 Мой профиль")
    kb.button(text="⚠️ Пожаловаться")
    if role in {"curator", "admin"}:
        kb.button(text="🛡️ Модерация")
        kb.button(text="🚩 Жалобы")
    if role == "admin":
        kb.button(text="👑 Админка")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)


def cancel_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text="❌ Отмена")
    return kb.as_markup(resize_keyboard=True)


def games_kb(names: list[str]) -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    for name in names:
        kb.button(text=f"🎮 {name}")
    kb.button(text="❌ Отмена")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)


def platforms_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    for name, icon in (
        ("PC", "💻"),
        ("PlayStation", "🎮"),
        ("Xbox", "🟩"),
        ("Mobile", "📱"),
    ):
        kb.button(text=f"{icon} {name}")
    kb.button(text="❌ Отмена")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)


def lobby_actions_kb(
    lobby_id: int, role: str, is_leader: bool
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if not is_leader:
        kb.button(text="⚔️ Откликнуться", callback_data=f"join:{lobby_id}")
    if role in {"curator", "admin"}:
        kb.button(text="🔒 Закрыть сбор", callback_data=f"mod:complete:{lobby_id}")
        kb.button(text="📦 В архив", callback_data=f"mod:archive:{lobby_id}")
    kb.adjust(1)
    return kb.as_markup()


def reports_kb(report_ids: list[int]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for rid in report_ids:
        kb.button(text=f"✅ Закрыть жалобу #{rid}", callback_data=f"report:close:{rid}")
    kb.adjust(1)
    return kb.as_markup()


def admin_menu_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text="➕ Добавить игру")
    kb.button(text="👋 Приветствие")
    kb.button(text="⏰ Прайм-тайм")
    kb.button(text="🎖️ Выдать роль")
    kb.button(text="⬅️ Назад")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)


def roles_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text="🎮 gamer")
    kb.button(text="🛡️ curator")
    kb.button(text="👑 admin")
    kb.button(text="❌ Отмена")
    kb.adjust(3)
    return kb.as_markup(resize_keyboard=True)