from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


def get_main_menu(role: str) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="👤 Мой профиль")
    builder.button(text="➕ Создать лобби")
    builder.button(text="🎮 Активные лобби")

    if role in ['manager', 'admin']:
        builder.button(text="🛠 Управление лобби")

    if role == 'admin':
        builder.button(text="👑 Назначить роль")

    builder.adjust(2, 1)
    return builder.as_markup(resize_keyboard=True)


# Отрисовка лобби с учетом того, является ли текущий пользователь автором (is_owner)
def get_lobby_kb(lobby_id: int, username: str, user_role: str, is_owner: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    # Ссылка на связь с создателем (показываем только если смотрит НЕ автор)
    if username and username != "Anonymous" and not is_owner:
        builder.button(text="💬 Написать автору", url=f"https://t.me/{username}")

    # Кнопка закрытия доступна автору ЛИБО менеджеру/админу
    if is_owner or user_role in ['manager', 'admin']:
        builder.button(text="❌ Закрыть лобби", callback_data=f"close_lobby:{lobby_id}")

    builder.adjust(1)
    return builder.as_markup()


def get_profile_actions_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Изменить профиль", callback_data="edit_profile")
    builder.button(text="🗑 Удалить профиль", callback_data="delete_profile")
    builder.adjust(2)
    return builder.as_markup()


def get_roles_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Игрок (user)", callback_data="set_role:user")
    builder.button(text="Менеджер (manager)", callback_data="set_role:manager")
    builder.button(text="Админ (admin)", callback_data="set_role:admin")
    builder.adjust(1)
    return builder.as_markup()

def get_cancel_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="❌ Отмена")
    return builder.as_markup(resize_keyboard=True)