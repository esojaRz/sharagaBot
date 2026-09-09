import re
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext

from states import ProfileForm, CreateLobbyForm, PlayerSearchForm
import keyboards as kb

user_router = Router()

# =====================================================================
# ВРЕМЕННОЕ ХРАНИЛИЩЕ
# =====================================================================
user_profiles = {}  # {user_id: {"game": ..., "rank": ..., "hours": ..., "prime_time": ..., "username": ...}}
active_lobbies = []
lobby_counter = 1


# =====================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ОЧИСТКИ СООБЩЕНИЙ
# =====================================================================

async def save_msg(state: FSMContext, msg_id: int):
    """Запоминает ID сообщения для будущего удаления."""
    data = await state.get_data()
    temp_msgs = data.get("temp_msgs", [])
    temp_msgs.append(msg_id)
    await state.update_data(temp_msgs=temp_msgs)


async def delete_temp_msgs(bot: Bot, chat_id: int, state: FSMContext):
    """Удаляет все накопленные временные сообщения (как бота, так и пользователя)."""
    data = await state.get_data()
    temp_msgs = data.get("temp_msgs", [])
    for msg_id in temp_msgs:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except Exception:
            pass
    await state.update_data(temp_msgs=[])


async def safe_delete_msg(message: Message):
    """Безопасное удаление одиночного сообщения."""
    try:
        await message.delete()
    except Exception:
        pass


# =====================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ФИЛЬТРАЦИИ И ПОИСКА
# =====================================================================

def parse_hours_int(val: str) -> int:
    numbers = re.findall(r'\d+', str(val))
    return int(numbers[0]) if numbers else 0


def check_hours_match(user_hours_str: str, filter_val: str) -> bool:
    if filter_val == "all":
        return True

    user_h = parse_hours_int(user_hours_str)

    if "-" in filter_val:
        try:
            min_h, max_h = map(int, filter_val.split("-"))
            return min_h <= user_h <= max_h
        except ValueError:
            pass

    min_required = parse_hours_int(filter_val)
    return user_h >= min_required if min_required > 0 else True


def check_prime_match(user_prime_str: str, filter_val: str) -> bool:
    if filter_val == "all":
        return True

    prime_map = {
        "06": ["утро", "06", "07", "08", "09", "10", "11", "12"],
        "12": ["день", "12", "13", "14", "15", "16", "17", "18"],
        "18": ["вечер", "18", "19", "20", "21", "22", "23", "00"],
        "00": ["ночь", "00", "01", "02", "03", "04", "05", "06"]
    }

    user_p_lower = str(user_prime_str).lower()

    if filter_val in prime_map:
        keywords = prime_map[filter_val]
        return any(kw in user_p_lower for kw in keywords)

    return filter_val.lower() in user_p_lower


# =====================================================================
# КОМАНДА /START И ОБЩАЯ ОТМЕНА
# =====================================================================

@user_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await delete_temp_msgs(message.bot, message.chat.id, state)
    await state.clear()
    await message.answer(
        f"Привет, **{message.from_user.full_name}**! 👋\n\n"
        "Добро пожаловать в сервис поиска тиммейтов и лобби для совместных игр.\n"
        "Используйте меню ниже для навигации.",
        reply_markup=kb.get_main_kb(),
        parse_mode="Markdown"
    )


@user_router.message(F.text == "❌ Отмена", StateFilter("*"))
@user_router.message(Command("cancel"), StateFilter("*"))
async def cancel_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return

    await delete_temp_msgs(message.bot, message.chat.id, state)
    await state.clear()
    await message.answer("❌ Действие отменено.", reply_markup=kb.get_main_kb())


# =====================================================================
# РАБОТА С ПРОФИЛЕМ ПОЛЬЗОВАТЕЛЯ
# =====================================================================

@user_router.message(F.text == "👤 Мой профиль")
async def show_profile(message: Message, state: FSMContext):
    await delete_temp_msgs(message.bot, message.chat.id, state)
    user_id = message.from_user.id

    if user_id in user_profiles:
        prof = user_profiles[user_id]
        text = (
            f"👤 **Ваш профиль:**\n\n"
            f"🎮 **Основная игра:** {prof['game']}\n"
            f"🎯 **Ранг / MMR:** {prof['rank']}\n"
            f"⏳ **Наиграно часов:** {prof['hours']}\n"
            f"⏰ **Прайм-тайм:** {prof['prime_time']}"
        )
        await message.answer(text, reply_markup=kb.get_profile_kb(), parse_mode="Markdown")
    else:
        await message.answer(
            "У вас пока нет заполненного профиля. Заполните его, чтобы другим игрокам было проще вас найти!",
            reply_markup=kb.get_no_profile_kb()
        )


@user_router.callback_query(F.data.in_({"create_profile", "edit_profile"}))
async def start_profile_creation(callback: CallbackQuery, state: FSMContext):
    await safe_delete_msg(callback.message)
    await state.clear()
    await state.set_state(ProfileForm.game)

    msg = await callback.message.answer(
        "🎮 **Шаг 1 из 4: Выберите игру из списка или введите название вручную:**",
        reply_markup=kb.get_games_keyboard(prefix="prof_game"),
        parse_mode="Markdown"
    )
    await save_msg(state, msg.message_id)
    await callback.answer()


@user_router.callback_query(F.data.startswith("prof_game_page:"), ProfileForm.game)
async def process_prof_game_page(callback: CallbackQuery):
    page = int(callback.data.split(":")[1])
    await callback.message.edit_reply_markup(reply_markup=kb.get_games_keyboard(prefix="prof_game", page=page))
    await callback.answer()


@user_router.callback_query(F.data.startswith("prof_game_select:"), ProfileForm.game)
async def process_prof_game_select(callback: CallbackQuery, state: FSMContext):
    await safe_delete_msg(callback.message)
    game = callback.data.split(":")[1]
    await state.update_data(game=game)
    await state.set_state(ProfileForm.rank)

    msg = await callback.message.answer(
        f"Выбрана игра: **{game}**\n\n🎯 **Шаг 2 из 4: Укажите ваш ранг / звание / MMR:**",
        reply_markup=kb.get_cancel_kb(),
        parse_mode="Markdown"
    )
    await save_msg(state, msg.message_id)
    await callback.answer()


@user_router.message(ProfileForm.game)
async def process_prof_game_text(message: Message, state: FSMContext):
    await save_msg(state, message.message_id)
    await state.update_data(game=message.text)
    await state.set_state(ProfileForm.rank)

    msg = await message.answer(
        f"Принято: **{message.text}**\n\n🎯 **Шаг 2 из 4: Укажите ваш ранг / звание / MMR:**",
        reply_markup=kb.get_cancel_kb(),
        parse_mode="Markdown"
    )
    await save_msg(state, msg.message_id)


@user_router.message(ProfileForm.rank)
async def process_prof_rank(message: Message, state: FSMContext):
    await save_msg(state, message.message_id)
    await state.update_data(rank=message.text)
    await state.set_state(ProfileForm.hours)

    msg = await message.answer(
        "⏳ **Шаг 3 из 4: Выберите наигранное количество часов или введите вручную:**",
        reply_markup=kb.get_profile_hours_kb(),
        parse_mode="Markdown"
    )
    await save_msg(state, msg.message_id)


@user_router.callback_query(F.data.startswith("prof_hours:"), ProfileForm.hours)
async def process_prof_hours_btn(callback: CallbackQuery, state: FSMContext):
    val = callback.data.split(":")[1]

    if val == "manual":
        prompt_msg = await callback.message.answer("Введите количество наигранных часов числом (например: `1200`):")
        await save_msg(state, prompt_msg.message_id)
        await callback.answer()
        return

    await safe_delete_msg(callback.message)
    await state.update_data(hours=val)
    await state.set_state(ProfileForm.prime_time)

    msg = await callback.message.answer(
        "⏰ **Шаг 4 из 4: Выберите ваш прайм-тайм или введите вручную:**",
        reply_markup=kb.get_profile_prime_kb(),
        parse_mode="Markdown"
    )
    await save_msg(state, msg.message_id)
    await callback.answer()


@user_router.message(ProfileForm.hours)
async def process_prof_hours_text(message: Message, state: FSMContext):
    await save_msg(state, message.message_id)
    await state.update_data(hours=message.text)
    await state.set_state(ProfileForm.prime_time)

    msg = await message.answer(
        "⏰ **Шаг 4 из 4: Выберите ваш прайм-тайм или введите вручную:**",
        reply_markup=kb.get_profile_prime_kb(),
        parse_mode="Markdown"
    )
    await save_msg(state, msg.message_id)


@user_router.callback_query(F.data.startswith("prof_prime:"), ProfileForm.prime_time)
async def process_prof_prime_btn(callback: CallbackQuery, state: FSMContext):
    val = callback.data.split(":")[1]

    if val == "manual":
        prompt_msg = await callback.message.answer("Введите ваш прайм-тайм текстом (например: `18:00 - 23:00 МСК`):")
        await save_msg(state, prompt_msg.message_id)
        await callback.answer()
        return

    await safe_delete_msg(callback.message)
    await state.update_data(prime_time=val)
    await finalize_profile(callback.message, state, callback.from_user)
    await callback.answer()


@user_router.message(ProfileForm.prime_time)
async def process_prof_prime_text(message: Message, state: FSMContext):
    await save_msg(state, message.message_id)
    await state.update_data(prime_time=message.text)
    await finalize_profile(message, state, message.from_user)


async def finalize_profile(message: Message, state: FSMContext, user):
    data = await state.get_data()

    user_profiles[user.id] = {
        "game": data["game"],
        "rank": data["rank"],
        "hours": data["hours"],
        "prime_time": data["prime_time"],
        "username": user.username or "без_юзернейма"
    }

    await delete_temp_msgs(message.bot, message.chat.id, state)
    await state.clear()

    await message.answer(
        "✅ **Профиль успешно сохранен!**",
        reply_markup=kb.get_main_kb(),
        parse_mode="Markdown"
    )


@user_router.callback_query(F.data == "delete_profile")
async def delete_profile_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id in user_profiles:
        del user_profiles[user_id]

    await callback.message.edit_text("🗑 Ваш профиль был успешно удален.")
    await callback.answer()


# =====================================================================
# СОЗДАНИЕ И ЗАКРЫТИЕ ЛОББИ
# =====================================================================

@user_router.message(F.text == "➕ Создать лобби", StateFilter("*"))
async def start_create_lobby(message: Message, state: FSMContext):
    await delete_temp_msgs(message.bot, message.chat.id, state)
    await state.clear()

    await state.set_state(CreateLobbyForm.game)
    msg = await message.answer(
        "🎮 **Шаг 1 из 4: Выберите игру для лобби из списка или введите вручную:**",
        reply_markup=kb.get_games_keyboard(prefix="lobby_game"),
        parse_mode="Markdown"
    )
    await save_msg(state, msg.message_id)


@user_router.callback_query(F.data.startswith("lobby_game_page:"), CreateLobbyForm.game)
async def process_lobby_game_page(callback: CallbackQuery):
    page = int(callback.data.split(":")[1])
    await callback.message.edit_reply_markup(reply_markup=kb.get_games_keyboard(prefix="lobby_game", page=page))
    await callback.answer()


@user_router.callback_query(F.data.startswith("lobby_game_select:"), CreateLobbyForm.game)
async def process_lobby_game_select(callback: CallbackQuery, state: FSMContext):
    await safe_delete_msg(callback.message)
    game = callback.data.split(":")[1]
    await state.update_data(game=game)
    await state.set_state(CreateLobbyForm.target_rank)

    msg = await callback.message.answer(
        f"Выбрана игра: **{game}**\n\n🎯 **Шаг 2 из 4: Какое минимальное звание / ранг ищете?**",
        reply_markup=kb.get_cancel_kb(),
        parse_mode="Markdown"
    )
    await save_msg(state, msg.message_id)
    await callback.answer()


@user_router.message(CreateLobbyForm.game)
async def process_lobby_game_text(message: Message, state: FSMContext):
    await save_msg(state, message.message_id)
    await state.update_data(game=message.text)
    await state.set_state(CreateLobbyForm.target_rank)

    msg = await message.answer(
        f"Принято: **{message.text}**\n\n🎯 **Шаг 2 из 4: Какое минимальное звание / ранг ищете?**",
        reply_markup=kb.get_cancel_kb(),
        parse_mode="Markdown"
    )
    await save_msg(state, msg.message_id)


@user_router.message(CreateLobbyForm.target_rank)
async def process_lobby_target_rank(message: Message, state: FSMContext):
    await save_msg(state, message.message_id)
    await state.update_data(target_rank=message.text)
    await state.set_state(CreateLobbyForm.slots)

    msg = await message.answer(
        "👥 **Шаг 3 из 4: Сколько игроков нужно найти?** (например: `+2` или `3`)",
        reply_markup=kb.get_cancel_kb(),
        parse_mode="Markdown"
    )
    await save_msg(state, msg.message_id)


@user_router.message(CreateLobbyForm.slots)
async def process_lobby_slots(message: Message, state: FSMContext):
    await save_msg(state, message.message_id)
    await state.update_data(slots=message.text)
    await state.set_state(CreateLobbyForm.description)

    msg = await message.answer(
        "📝 **Шаг 4 из 4: Напишите краткое описание лобби / комментарий:**",
        reply_markup=kb.get_cancel_kb(),
        parse_mode="Markdown"
    )
    await save_msg(state, msg.message_id)


@user_router.message(CreateLobbyForm.description)
async def process_lobby_description(message: Message, state: FSMContext):
    global lobby_counter
    await save_msg(state, message.message_id)
    await state.update_data(description=message.text)
    data = await state.get_data()

    username = message.from_user.username
    if not username:
        await message.answer(
            "⚠️ У вас не установлен Telegram Username (@username). Другие игроки не смогут написать вам в ЛС!")

    lobby_data = {
        "id": lobby_counter,
        "user_id": message.from_user.id,
        "username": username or "инкогнито",
        "game": data["game"],
        "target_rank": data["target_rank"],
        "slots": data["slots"],
        "description": data["description"]
    }
    active_lobbies.append(lobby_data)
    lobby_counter += 1

    await delete_temp_msgs(message.bot, message.chat.id, state)
    await state.clear()

    await message.answer(
        f"✅ **Лобби #{lobby_data['id']} успешно опубликовано!**",
        reply_markup=kb.get_main_kb(),
        parse_mode="Markdown"
    )


@user_router.callback_query(F.data.startswith("close_lobby:"))
async def close_lobby_handler(callback: CallbackQuery):
    lobby_id = int(callback.data.split(":")[1])
    global active_lobbies

    lobby = next((l for l in active_lobbies if l["id"] == lobby_id), None)
    if lobby:
        if lobby["user_id"] == callback.from_user.id:
            active_lobbies = [l for l in active_lobbies if l["id"] != lobby_id]
            await callback.message.edit_text(f"❌ Лобби #{lobby_id} закрыто автором.")
        else:
            await callback.answer("Вы не являетесь владельцем этого лобби!", show_alert=True)
    else:
        await callback.message.edit_text("Лобби уже закрыто или не существует.")
    await callback.answer()


# =====================================================================
# ПОИСК И ПРОСМОТР ЛОББИ
# =====================================================================

@user_router.message(F.text == "📋 Найти лобби")
async def list_lobbies(message: Message, state: FSMContext):
    await delete_temp_msgs(message.bot, message.chat.id, state)
    if not active_lobbies:
        await message.answer("😔 На данный момент активных лобби нет. Будьте первыми и создайте свое!")
        return

    games = list({l["game"] for l in active_lobbies})

    msg = await message.answer(
        "🔎 **Выберите фильтр по игре или посмотрите все открытые лобби:**",
        reply_markup=kb.get_games_filter_kb(games),
        parse_mode="Markdown"
    )
    await save_msg(state, msg.message_id)


@user_router.callback_query(F.data.startswith("filter_game:"))
async def filter_lobbies_callback(callback: CallbackQuery, state: FSMContext):
    await safe_delete_msg(callback.message)
    selected_game = callback.data.split(":")[1]

    filtered = active_lobbies if selected_game == "all" else [l for l in active_lobbies if l["game"] == selected_game]

    if not filtered:
        await callback.message.answer("По данному фильтру лобби не найдены.")
        await callback.answer()
        return

    for l in filtered:
        text = (
            f"🎮 **Игра:** {l['game']}\n"
            f"🎯 **Нужен ранг:** {l['target_rank']}\n"
            f"👥 **Свободно мест:** {l['slots']}\n"
            f"📝 **Описание:** {l['description']}\n"
            f"👤 **Организатор:** @{l['username']}"
        )

        reply_markup = kb.get_close_lobby_kb(l["id"]) if l["user_id"] == callback.from_user.id else (
            kb.get_contact_kb(l["username"]) if l["username"] != "инкогнито" else None
        )

        await callback.message.answer(text, reply_markup=reply_markup, parse_mode="Markdown")

    await callback.answer()


# =====================================================================
# ПОИСК ИГРОКОВ (С ПОЛНЫМ УДАЛЕНИЕМ СТАРЫХ КНОПОК)
# =====================================================================

@user_router.message(F.text == "🔍 Найти игроков")
async def search_players_start(message: Message, state: FSMContext):
    await delete_temp_msgs(message.bot, message.chat.id, state)
    await state.clear()

    if not user_profiles:
        await message.answer("Пока никто не зарегистрировал свой профиль.")
        return

    games = list({p["game"] for p in user_profiles.values()})
    msg = await message.answer(
        "🔍 **Шаг 1 из 3: Выберите игру для поиска соратников:**",
        reply_markup=kb.get_player_filter_kb(games),
        parse_mode="Markdown"
    )
    await save_msg(state, msg.message_id)


@user_router.callback_query(F.data.startswith("filter_player_game:"))
async def process_search_game_filter(callback: CallbackQuery, state: FSMContext):
    await safe_delete_msg(callback.message)
    game = callback.data.split(":")[1]
    await state.update_data(search_game=game)
    await state.set_state(PlayerSearchForm.hours)

    msg = await callback.message.answer(
        "⏳ **Шаг 2 из 3: Укажите предпочтительное количество часов:**",
        reply_markup=kb.get_hours_filter_kb(),
        parse_mode="Markdown"
    )
    await save_msg(state, msg.message_id)
    await callback.answer()


@user_router.callback_query(F.data.startswith("search_hours:"), PlayerSearchForm.hours)
async def process_search_hours_filter(callback: CallbackQuery, state: FSMContext):
    choice = callback.data.split(":")[1]

    if choice == "manual":
        prompt_msg = await callback.message.answer("Введите минимальное количество часов числом (например: `500`):")
        await save_msg(state, prompt_msg.message_id)
        await callback.answer()
        return

    await safe_delete_msg(callback.message)
    await state.update_data(search_hours=choice)
    await state.set_state(PlayerSearchForm.prime_time)

    msg = await callback.message.answer(
        "⏰ **Шаг 3 из 3: Укажите предпочтительный прайм-тайм:**",
        reply_markup=kb.get_prime_filter_kb(),
        parse_mode="Markdown"
    )
    await save_msg(state, msg.message_id)
    await callback.answer()


@user_router.message(PlayerSearchForm.hours)
async def process_search_hours_text(message: Message, state: FSMContext):
    await save_msg(state, message.message_id)
    await state.update_data(search_hours=message.text)
    await state.set_state(PlayerSearchForm.prime_time)

    msg = await message.answer(
        "⏰ **Шаг 3 из 3: Укажите предпочтительный прайм-тайм:**",
        reply_markup=kb.get_prime_filter_kb(),
        parse_mode="Markdown"
    )
    await save_msg(state, msg.message_id)


@user_router.callback_query(F.data.startswith("search_prime:"), PlayerSearchForm.prime_time)
async def process_search_prime_filter(callback: CallbackQuery, state: FSMContext):
    choice = callback.data.split(":")[1]

    if choice == "manual":
        prompt_msg = await callback.message.answer("Введите желаемый прайм-тайм или город/часовой пояс текстом:")
        await save_msg(state, prompt_msg.message_id)
        await callback.answer()
        return

    await safe_delete_msg(callback.message)
    await state.update_data(search_prime=choice)
    await show_search_results(callback.message, state)
    await callback.answer()


@user_router.message(PlayerSearchForm.prime_time)
async def process_search_prime_text(message: Message, state: FSMContext):
    await save_msg(state, message.message_id)
    await state.update_data(search_prime=message.text)
    await show_search_results(message, state)


async def show_search_results(message: Message, state: FSMContext):
    data = await state.get_data()

    target_game = data.get("search_game", "all")
    target_hours = data.get("search_hours", "all")
    target_prime = data.get("search_prime", "all")

    await delete_temp_msgs(message.bot, message.chat.id, state)
    await state.clear()

    results = []
    for uid, prof in user_profiles.items():
        if uid == message.from_user.id:
            continue

        if target_game != "all" and prof["game"].lower() != target_game.lower():
            continue

        if not check_hours_match(prof["hours"], target_hours):
            continue

        if not check_prime_match(prof["prime_time"], target_prime):
            continue

        results.append(prof)

    if not results:
        await message.answer("😔 К сожалению, подходящих игроков по вашим критериям не найдено.")
        return

    await message.answer(f"🎉 Найдено анкет игроков: **{len(results)}**")
    for prof in results:
        text = (
            f"👤 **Игрок:** @{prof['username']}\n"
            f"🎮 **Игра:** {prof['game']}\n"
            f"🎯 **Ранг / MMR:** {prof['rank']}\n"
            f"⏳ **Часов:** {prof['hours']}\n"
            f"⏰ **Прайм-тайм:** {prof['prime_time']}"
        )
        markup = kb.get_player_contact_kb(prof['username']) if prof['username'] != "без_юзернейма" else None
        await message.answer(text, reply_markup=markup, parse_mode="Markdown")