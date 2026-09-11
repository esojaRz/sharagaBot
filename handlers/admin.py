from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

import database as db
from config import ROLE_ADMIN, ROLE_CURATOR, ROLE_GAMER
from keyboards import admin_menu_kb, cancel_kb, main_menu, roles_kb
from states import AdminGameSG, AdminRoleSG, AdminSettingSG

router = Router()

ALLOWED_ROLES = {ROLE_GAMER, ROLE_CURATOR, ROLE_ADMIN}


@router.message(F.text == "Админка")
async def admin_home(message: Message, state: FSMContext) -> None:
    await state.clear()
    user = await db.get_user(message.from_user.id)
    if user is None or user["role"] != ROLE_ADMIN:
        await message.answer("Только для админа.")
        return
    games = await db.list_games()
    names = ", ".join(g["name"] for g in games) or "пусто"
    welcome = await db.get_setting("welcome_text")
    prime = await db.get_setting("prime_hint")
    await message.answer(
        f"Глобальные настройки\n"
        f"Игры: {names}\n"
        f"Приветствие: {welcome}\n"
        f"Прайм-тайм: {prime}",
        reply_markup=admin_menu_kb(),
    )


@router.message(F.text == "Добавить игру")
async def add_game_start(message: Message, state: FSMContext) -> None:
    user = await db.get_user(message.from_user.id)
    if user is None or user["role"] != ROLE_ADMIN:
        return
    await state.set_state(AdminGameSG.name)
    await message.answer("Название дисциплины (2–32 символа).", reply_markup=cancel_kb())


@router.message(AdminGameSG.name)
async def add_game_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if not (2 <= len(name) <= 32):
        await message.answer("Название: 2–32 символа.")
        return
    if await db.get_game(name):
        await message.answer("Такая игра уже есть.")
        return
    await state.update_data(name=name)
    await state.set_state(AdminGameSG.max_party)
    await message.answer("Максимум игроков в пати для этой игры (число 2–5).")


@router.message(AdminGameSG.max_party)
async def add_game_size(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip()
    if not raw.isdigit() or not (2 <= int(raw) <= 5):
        await message.answer("Нужно число от 2 до 5.")
        return
    data = await state.get_data()
    await db.add_game(data["name"], int(raw))
    await state.clear()
    await message.answer(f"Игра {data['name']} добавлена (формат {raw}).", reply_markup=admin_menu_kb())


@router.message(F.text == "Приветствие")
async def welcome_start(message: Message, state: FSMContext) -> None:
    user = await db.get_user(message.from_user.id)
    if user is None or user["role"] != ROLE_ADMIN:
        return
    await state.update_data(setting_key="welcome_text")
    await state.set_state(AdminSettingSG.value)
    await message.answer("Новый текст /start (10–300 символов).", reply_markup=cancel_kb())


@router.message(F.text == "Прайм-тайм")
async def prime_start(message: Message, state: FSMContext) -> None:
    user = await db.get_user(message.from_user.id)
    if user is None or user["role"] != ROLE_ADMIN:
        return
    await state.update_data(setting_key="prime_hint")
    await state.set_state(AdminSettingSG.value)
    await message.answer("Подсказка прайм-тайма, например 19:00-23:00.", reply_markup=cancel_kb())


@router.message(AdminSettingSG.value)
async def save_setting(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()
    if not (4 <= len(value) <= 300):
        await message.answer("Длина 4–300 символов.")
        return
    data = await state.get_data()
    await db.set_setting(data["setting_key"], value)
    await state.clear()
    await message.answer("Настройка сохранена.", reply_markup=admin_menu_kb())


@router.message(F.text == "Выдать роль")
async def role_start(message: Message, state: FSMContext) -> None:
    user = await db.get_user(message.from_user.id)
    if user is None or user["role"] != ROLE_ADMIN:
        return
    await state.set_state(AdminRoleSG.user_id)
    await message.answer("Telegram ID пользователя (число).", reply_markup=cancel_kb())


@router.message(AdminRoleSG.user_id)
async def role_user(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip()
    if not raw.isdigit():
        await message.answer("Нужен числовой Telegram ID.")
        return
    target = await db.get_user(int(raw))
    if target is None:
        await message.answer("Пользователь не регистрировался в боте.")
        return
    await state.update_data(user_id=int(raw))
    await state.set_state(AdminRoleSG.role)
    await message.answer("Роль: gamer, curator или admin.", reply_markup=roles_kb())


@router.message(AdminRoleSG.role)
async def role_set(message: Message, state: FSMContext) -> None:
    role = (message.text or "").strip()
    if role not in ALLOWED_ROLES:
        await message.answer("Только gamer / curator / admin.")
        return
    data = await state.get_data()
    await db.set_user_role(data["user_id"], role)
    await state.clear()
    await message.answer(f"Роль {role} выдана user {data['user_id']}.", reply_markup=admin_menu_kb())
