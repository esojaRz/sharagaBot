from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

import database as db
from config import ROLE_LABELS
from keyboards import cancel_kb, main_menu
from states import RegisterSG

router = Router()


def profile_text(user) -> str:
    return (
        f"Профиль\n"
        f"Ник: {user['nick']}\n"
        f"Роль: {ROLE_LABELS.get(user['role'], user['role'])}\n"
        f"Стаж: {user['experience_years']} лет\n"
        f"Язык связи: {user['language']}"
    )


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    user = await db.get_user(message.from_user.id)
    welcome = await db.get_setting("welcome_text")
    if user is None:
        await message.answer(
            f"{welcome}\n\nРегистрация: как тебя звать в лобби? Ник 2–24 символа.",
            reply_markup=cancel_kb(),
        )
        await state.set_state(RegisterSG.nick)
        return
    await message.answer(welcome, reply_markup=main_menu(user["role"]))


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "Команды:\n"
        "/start — меню\n"
        "/cancel — выйти из формы\n\n"
        "Геймер собирает лобби и откликается на чужие.\n"
        "Куратор модерирует сборы и жалобы.\n"
        "Админ добавляет игры и меняет настройки."
    )


@router.message(Command("cancel"))
@router.message(F.text == "Отмена")
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    user = await db.get_user(message.from_user.id)
    if user is None:
        await message.answer("Ок. Напиши /start, чтобы зарегистрироваться.")
        return
    await message.answer("Форма сброшена.", reply_markup=main_menu(user["role"]))


@router.message(F.text == "Назад")
async def go_back(message: Message, state: FSMContext) -> None:
    await state.clear()
    user = await db.get_user(message.from_user.id)
    if user is None:
        await message.answer("Сначала /start")
        return
    await message.answer("Главное меню", reply_markup=main_menu(user["role"]))


@router.message(F.text == "Мой профиль")
async def my_profile(message: Message) -> None:
    user = await db.get_user(message.from_user.id)
    if user is None:
        await message.answer("Сначала /start")
        return
    await message.answer(profile_text(user), reply_markup=main_menu(user["role"]))


@router.message(RegisterSG.nick)
async def reg_nick(message: Message, state: FSMContext) -> None:
    nick = (message.text or "").strip()
    if not (2 <= len(nick) <= 24):
        await message.answer("Ник должен быть от 2 до 24 символов.")
        return
    await state.update_data(nick=nick)
    await state.set_state(RegisterSG.experience)
    await message.answer("Сколько лет играешь? Число от 0 до 40.")


@router.message(RegisterSG.experience)
async def reg_exp(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not text.isdigit() or not (0 <= int(text) <= 40):
        await message.answer("Нужно целое число от 0 до 40.")
        return
    await state.update_data(experience=int(text))
    await state.set_state(RegisterSG.language)
    await message.answer("Основной язык связи (ru, en, …). 2–8 символов.")


@router.message(RegisterSG.language)
async def reg_lang(message: Message, state: FSMContext) -> None:
    lang = (message.text or "").strip().lower()
    if not (2 <= len(lang) <= 8) or not lang.isalpha():
        await message.answer("Язык — только буквы, 2–8 символов.")
        return
    data = await state.get_data()
    await db.create_user(message.from_user.id, data["nick"], data["experience"], lang)
    await state.clear()
    user = await db.get_user(message.from_user.id)
    await message.answer(
        "Готово. Добро пожаловать в LFG.\n\n" + profile_text(user),
        reply_markup=main_menu(user["role"]),
    )
