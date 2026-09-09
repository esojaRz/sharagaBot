import logging
import re
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from states import ProfileForm, CreateLobbyForm
import database as db
import keyboards as kb

user_router = Router()

TIME_PATTERN = re.compile(
    r"^([0-1]?\d|2[0-3])[:.][0-5]\d(\s*[-—–]\s*([0-1]?\d|2[0-3])[:.][0-5]\d)?(\s+.*)?$",
    re.IGNORECASE
)


# =====================================================================
# 1. СТАРТ И ОБРАБОТЧИК ОТМЕНЫ
# =====================================================================

@user_router.message(Command("start"), StateFilter("*"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await db.get_or_create_user(message.from_user.id, message.from_user.username or "Anonymous")
    role = await db.get_user_role(message.from_user.id)

    await message.answer(
        "🎮 **LFG: Game Matchmaker**\n\nИспользуйте меню ниже для навигации:",
        reply_markup=kb.get_main_menu(role)
    )


# Кнопка «Отмена» или команда /cancel (сбрасывает любое состояние)
@user_router.message(F.text == "❌ Отмена", StateFilter("*"))
@user_router.message(Command("cancel"), StateFilter("*"))
async def cancel_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()
    await state.clear()

    role = await db.get_user_role(message.from_user.id)

    if current_state is None:
        await message.answer("Нечего отменять.", reply_markup=kb.get_main_menu(role))
    else:
        await message.answer("❌ Действие отменено.", reply_markup=kb.get_main_menu(role))


# =====================================================================
# 2. ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ
# =====================================================================

@user_router.message(F.text == "👤 Мой профиль", StateFilter("*"))
async def show_profile(message: Message, state: FSMContext):
    await state.clear()
    try:
        profile = await db.get_user_profile(message.from_user.id)

        if profile and profile[0]:
            game, rank, hours, prime_time = profile
            text = (
                f"👤 **Ваш профиль:**\n\n"
                f"🎮 Игра: **{game}**\n"
                f"🎯 Ранг: **{rank}**\n"
                f"⏳ Наиграно: **{hours} ч.**\n"
                f"🕒 Прайм-тайм: **{prime_time}**"
            )
            await message.answer(text, reply_markup=kb.get_profile_actions_kb())
        else:
            await state.set_state(ProfileForm.game)
            await message.answer(
                "У вас еще нет заполненного профиля.\n\nУкажите дисциплину (например, CS2, Dota 2, Valorant):",
                reply_markup=kb.get_cancel_kb()
            )
    except Exception as e:
        logging.error(f"Ошибка при получении профиля: {e}")
        await message.answer("⚠️ Ошибка загрузки профиля. Нажмите /start")


@user_router.callback_query(F.data == "edit_profile", StateFilter("*"))
async def start_edit_profile(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(ProfileForm.game)
    await callback.message.answer(
        "Укажите дисциплину (например, CS2, Dota 2, Valorant):",
        reply_markup=kb.get_cancel_kb()
    )
    await callback.answer()


@user_router.callback_query(F.data == "delete_profile", StateFilter("*"))
async def process_delete_profile(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await db.delete_user_profile(callback.from_user.id)
    await callback.message.edit_text("🗑 Ваш профиль успешно удален.")
    await callback.answer("Профиль удален")


# --- Шаги анкеты профиля (FSM) ---

@user_router.message(ProfileForm.game)
async def process_game(message: Message, state: FSMContext):
    await state.update_data(game=message.text)
    await state.set_state(ProfileForm.rank)
    await message.answer("Укажите ваш ранг/звание:", reply_markup=kb.get_cancel_kb())


@user_router.message(ProfileForm.rank)
async def process_rank(message: Message, state: FSMContext):
    await state.update_data(rank=message.text)
    await state.set_state(ProfileForm.hours)
    await message.answer("Сколько часов наиграно? (Введите только число):", reply_markup=kb.get_cancel_kb())


@user_router.message(ProfileForm.hours)
async def process_hours(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) < 0:
        await message.answer("⚠️ Введите корректное положительное число часов:", reply_markup=kb.get_cancel_kb())
        return
    await state.update_data(hours=int(message.text))
    await state.set_state(ProfileForm.prime_time)
    await message.answer("Укажите прайм-тайм (например, 18:00 - 22:00 МСК):", reply_markup=kb.get_cancel_kb())


@user_router.message(ProfileForm.prime_time)
async def process_prime(message: Message, state: FSMContext):
    text = message.text.strip()

    if not TIME_PATTERN.match(text):
        await message.answer(
            "⚠️ **Неверный формат времени!**\n\n"
            "Время или диапазон времени нужно указывать **через двоеточие (:) или точку (.)**.\n\n"
            "📌 **Примеры:** `18:00`, `18.00`, `18:00 - 22:00`",
            reply_markup=kb.get_cancel_kb()
        )
        return

    await state.update_data(prime_time=text)
    data = await state.get_data()

    await db.update_user_profile(
        user_id=message.from_user.id,
        game=data['game'],
        rank=data['rank'],
        hours=data['hours'],
        prime_time=data['prime_time'],
        username=message.from_user.username or "Anonymous"
    )
    await state.clear()

    role = await db.get_user_role(message.from_user.id)
    await message.answer("✅ Профиль успешно обновлен!", reply_markup=kb.get_main_menu(role))


# =====================================================================
# 3. СОЗДАНИЕ ЛОББИ (FSM)
# =====================================================================

@user_router.message(F.text == "➕ Создать лобби", StateFilter("*"))
async def start_lobby(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(CreateLobbyForm.game)
    await message.answer("Для какой игры ищете пати?", reply_markup=kb.get_cancel_kb())


@user_router.message(CreateLobbyForm.game)
async def lobby_game(message: Message, state: FSMContext):
    await state.update_data(game=message.text)
    await state.set_state(CreateLobbyForm.target_rank)
    await message.answer("Минимальный требуемый ранг:", reply_markup=kb.get_cancel_kb())


@user_router.message(CreateLobbyForm.target_rank)
async def lobby_rank(message: Message, state: FSMContext):
    await state.update_data(target_rank=message.text)
    await state.set_state(CreateLobbyForm.slots)
    await message.answer("Сколько человек нужно найти? (Введите число от 1 до 10):", reply_markup=kb.get_cancel_kb())


@user_router.message(CreateLobbyForm.slots)
async def lobby_slots(message: Message, state: FSMContext):
    if not message.text.isdigit() or not (1 <= int(message.text) <= 10):
        await message.answer("⚠️ Введите число от 1 до 10:", reply_markup=kb.get_cancel_kb())
        return
    await state.update_data(slots=int(message.text))
    await state.set_state(CreateLobbyForm.description)
    await message.answer("Добавьте комментарий (например, 'Нужен саппорт в дискорд'):", reply_markup=kb.get_cancel_kb())


@user_router.message(CreateLobbyForm.description)
async def lobby_desc(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    data = await state.get_data()
    role = await db.get_user_role(message.from_user.id)

    try:
        await db.create_order(
            message.from_user.id, data['game'], data['target_rank'], data['slots'], data['description']
        )
        await state.clear()
        await message.answer("🎯 Лобби успешно создано!", reply_markup=kb.get_main_menu(role))
    except Exception as e:
        logging.error(f"Ошибка при создании лобби: {e}")
        await message.answer("⚠️ Не удалось создать лобби. Попробуйте еще раз.", reply_markup=kb.get_main_menu(role))


# =====================================================================
# 4. ПРОСМОТР АКТИВНЫХ ЛОББИ
# =====================================================================

@user_router.message(F.text == "🎮 Активные лобби", StateFilter("*"))
async def list_lobbies(message: Message, state: FSMContext):
    await state.clear()
    orders = await db.get_active_orders()
    if not orders:
        await message.answer("В данный момент нет активных лобби.")
        return

    user_role = await db.get_user_role(message.from_user.id)
    current_user_id = message.from_user.id

    for order in orders:
        order_id, game, rank, slots, desc, username, owner_id = order
        is_owner = (current_user_id == owner_id)
        author_label = f"@{username} (Вы)" if is_owner else f"@{username}"

        text = (
            f"🆔 **Лобби #{order_id}** | **{game}**\n"
            f"🎯 Минимальный ранг: {rank}\n"
            f"👥 Требуется игроков: {slots}\n"
            f"📝 {desc}\n"
            f"👤 Автор: {author_label}"
        )
        await message.answer(
            text,
            reply_markup=kb.get_lobby_kb(order_id, username, user_role, is_owner=is_owner)
        )