from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


# =====================================================================
# REPLY-КЛАВИАТУРЫ (НИЖНЕЕ МЕНЮ)
# =====================================================================

def get_main_kb() -> ReplyKeyboardMarkup:
    """Главное меню бота."""
    builder = ReplyKeyboardBuilder()
    builder.button(text="👤 Мой профиль")
    builder.button(text="➕ Создать лобби")
    builder.button(text="📋 Найти лобби")
    builder.button(text="🔍 Найти игроков")
    builder.adjust(2, 2)
    return builder.as_markup(resize_keyboard=True)


def get_cancel_kb() -> ReplyKeyboardMarkup:
    """Кнопка отмены для FSM-форм."""
    builder = ReplyKeyboardBuilder()
    builder.button(text="❌ Отмена")
    return builder.as_markup(resize_keyboard=True)


# =====================================================================
# INLINE-КЛАВИАТУРЫ ПРОФИЛЯ
# =====================================================================

def get_profile_kb() -> InlineKeyboardMarkup:
    """Действия с заполненным профилем."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Редактировать", callback_data="edit_profile")
    builder.button(text="🗑 Удалить профиль", callback_data="delete_profile")
    builder.adjust(2)
    return builder.as_markup()


def get_no_profile_kb() -> InlineKeyboardMarkup:
    """Кнопка создания профиля, если его нет."""
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Заполнить профиль", callback_data="create_profile")
    return builder.as_markup()


def get_profile_hours_kb() -> InlineKeyboardMarkup:
    """Клавиатура выбора часов при создании профиля."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🥉 До 100 ч.", callback_data="prof_hours:До 100 ч.")
    builder.button(text="🥈 100 - 500 ч.", callback_data="prof_hours:100 - 500 ч.")
    builder.button(text="🥇 500 - 1000 ч.", callback_data="prof_hours:500 - 1000 ч.")
    builder.button(text="🏆 1000+ ч.", callback_data="prof_hours:1000+ ч.")
    builder.button(text="✏️ Ввести число вручную", callback_data="prof_hours:manual")
    builder.adjust(2, 2, 1)
    return builder.as_markup()


def get_profile_prime_kb() -> InlineKeyboardMarkup:
    """Клавиатура выбора прайм-тайма при создании профиля."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🌅 Утро (06:00 - 12:00)", callback_data="prof_prime:06:00 - 12:00 МСК")
    builder.button(text="☀️ День (12:00 - 18:00)", callback_data="prof_prime:12:00 - 18:00 МСК")
    builder.button(text="🌆 Вечер (18:00 - 00:00)", callback_data="prof_prime:18:00 - 00:00 МСК")
    builder.button(text="🌙 Ночь (00:00 - 06:00)", callback_data="prof_prime:00:00 - 06:00 МСК")
    builder.button(text="✏️ Ввести вручную", callback_data="prof_prime:manual")
    builder.adjust(2, 2, 1)
    return builder.as_markup()


# =====================================================================
# INLINE-КЛАВИАТУРЫ ПОИСКА И ФИЛЬТРОВ
# =====================================================================

def get_games_filter_kb(games: list) -> InlineKeyboardMarkup:
    """Фильтр по играм для лобби."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🌐 Все игры", callback_data="filter_game:all")
    for game in games:
        builder.button(text=game, callback_data=f"filter_game:{game}")
    builder.adjust(1)
    return builder.as_markup()


def get_player_filter_kb(games: list) -> InlineKeyboardMarkup:
    """Фильтр по играм для поиска игроков."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🌐 Все игры", callback_data="filter_player_game:all")
    for game in games:
        builder.button(text=game, callback_data=f"filter_player_game:{game}")
    builder.adjust(1)
    return builder.as_markup()


def get_hours_filter_kb() -> InlineKeyboardMarkup:
    """Фильтр по часам при поиске игроков."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🌐 Любое кол-во часов", callback_data="search_hours:all")
    builder.button(text="🥉 До 100 ч.", callback_data="search_hours:0-100")
    builder.button(text="🥈 100 - 500 ч.", callback_data="search_hours:100-500")
    builder.button(text="🥇 500 - 1000 ч.", callback_data="search_hours:500-1000")
    builder.button(text="🏆 1000+ ч.", callback_data="search_hours:1000-999999")
    builder.button(text="✏️ Мин. часов вручную", callback_data="search_hours:manual")
    builder.adjust(1, 2, 2, 1)
    return builder.as_markup()


def get_prime_filter_kb() -> InlineKeyboardMarkup:
    """Фильтр по прайм-тайму при поиске игроков."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🌐 Любое время", callback_data="search_prime:all")
    builder.button(text="🌅 Утро (06:00 - 12:00)", callback_data="search_prime:06")
    builder.button(text="☀️ День (12:00 - 18:00)", callback_data="search_prime:12")
    builder.button(text="🌆 Вечер (18:00 - 00:00)", callback_data="search_prime:18")
    builder.button(text="🌙 Ночь (00:00 - 06:00)", callback_data="search_prime:00")
    builder.button(text="✏️ Текст/Город вручную", callback_data="search_prime:manual")
    builder.adjust(1, 2, 2, 1)
    return builder.as_markup()


# =====================================================================
# ВЫБОР ИГР (ПАСПОРТ/ПАГИНАЦИЯ)
# =====================================================================

PRESET_GAMES = [
    "CS2", "Dota 2", "Valorant", "Apex Legends",
    "PUBG", "Rust", "Overwatch 2", "Rainbow Six Siege",
    "League of Legends", "GTA V", "Fortnite", "Minecraft"
]


def get_games_keyboard(prefix: str, page: int = 0) -> InlineKeyboardMarkup:
    """Генерация клавиатуры выбора популярных игр с пагинацией."""
    builder = InlineKeyboardBuilder()
    items_per_page = 6
    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page

    current_games = PRESET_GAMES[start_idx:end_idx]

    for game in current_games:
        builder.button(text=game, callback_data=f"{prefix}_select:{game}")

    builder.adjust(2)

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"{prefix}_page:{page - 1}"))
    if end_idx < len(PRESET_GAMES):
        nav_buttons.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"{prefix}_page:{page + 1}"))

    if nav_buttons:
        builder.row(*nav_buttons)

    return builder.as_markup()


# =====================================================================
# КНОПКИ ДЕЙСТВИЙ (СВЯЗЬ И ЗАКРЫТИЕ)
# =====================================================================

def get_contact_kb(username: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="💬 Написать", url=f"https://t.me/{username}")
    return builder.as_markup()


def get_player_contact_kb(username: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="💬 Написать игроку", url=f"https://t.me/{username}")
    return builder.as_markup()


def get_close_lobby_kb(lobby_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Закрыть лобби", callback_data=f"close_lobby:{lobby_id}")
    return builder.as_markup()