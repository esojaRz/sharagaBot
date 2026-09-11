from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import database as db
from config import STATUS_LABELS
from keyboards import cancel_kb, games_kb, lobby_actions_kb, main_menu, platforms_kb
from states import LobbyCreateSG, ReportSG

router = Router()


def lobby_card(row) -> str:
    return (
        f"Лобби #{row['id']}\n"
        f"Игра: {row['game']}\n"
        f"Платформа: {row['platform']}\n"
        f"Ранг: {row['required_rank']}\n"
        f"Старт: {row['start_time']}\n"
        f"Свободно мест: {row['free_slots']} / формат {row['max_party']}\n"
        f"Лидер: {row['leader_nick']}\n"
        f"Статус: {STATUS_LABELS.get(row['status'], row['status'])}"
    )


@router.message(F.text == "Создать лобби")
async def start_create(message: Message, state: FSMContext) -> None:
    user = await db.get_user(message.from_user.id)
    if user is None:
        await message.answer("Сначала /start")
        return
    games = await db.list_games()
    if not games:
        await message.answer("Игр пока нет. Админ должен добавить дисциплину.")
        return
    await state.set_state(LobbyCreateSG.game)
    await message.answer(
        "Выбери игру из списка.",
        reply_markup=games_kb([g["name"] for g in games]),
    )


@router.message(LobbyCreateSG.game)
async def pick_game(message: Message, state: FSMContext) -> None:
    game = await db.get_game((message.text or "").strip())
    if game is None:
        await message.answer("Такой игры нет. Выбери кнопку из списка.")
        return
    await state.update_data(game=game["name"], max_party=game["max_party"])
    await state.set_state(LobbyCreateSG.platform)
    await message.answer("Платформа?", reply_markup=platforms_kb())


@router.message(LobbyCreateSG.platform)
async def pick_platform(message: Message, state: FSMContext) -> None:
    platform = (message.text or "").strip()
    if platform not in {"PC", "PlayStation", "Xbox", "Mobile"}:
        await message.answer("Выбери платформу кнопкой.")
        return
    await state.update_data(platform=platform)
    await state.set_state(LobbyCreateSG.rank)
    await message.answer("Нужный ранг / уровень (например Gold 2, Immortal). 2–32 символа.", reply_markup=cancel_kb())


@router.message(LobbyCreateSG.rank)
async def pick_rank(message: Message, state: FSMContext) -> None:
    rank = (message.text or "").strip()
    if not (2 <= len(rank) <= 32):
        await message.answer("Ранг: от 2 до 32 символов.")
        return
    await state.update_data(rank=rank)
    await state.set_state(LobbyCreateSG.start_time)
    prime = await db.get_setting("prime_hint")
    await message.answer(
        f"Время старта катки. Пример прайм-тайма: {prime or '19:00'}.\n"
        "Формат: ЧЧ:ММ, например 21:30."
    )


@router.message(LobbyCreateSG.start_time)
async def pick_time(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip()
    parts = raw.split(":")
    if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
        await message.answer("Нужен формат ЧЧ:ММ, например 19:00.")
        return
    hour, minute = int(parts[0]), int(parts[1])
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        await message.answer("Часы 0–23, минуты 0–59.")
        return
    await state.update_data(start_time=f"{hour:02d}:{minute:02d}")
    data = await state.get_data()
    max_needed = min(5, int(data["max_party"]) - 1)
    if max_needed < 1:
        max_needed = 1
    await state.update_data(max_needed=max_needed)
    await state.set_state(LobbyCreateSG.slots)
    await message.answer(
        f"Сколько игроков ещё нужно в пати?\n"
        f"Только число от 1 до {max_needed} (формат {data['game']}: {data['max_party']} слотов, лидер уже в лобби)."
    )


@router.message(LobbyCreateSG.slots)
async def pick_slots(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip()
    data = await state.get_data()
    max_needed = int(data.get("max_needed", 5))
    if not raw.isdigit():
        await message.answer(f"Только цифры. Нужно целое число от 1 до {max_needed}.")
        return
    slots = int(raw)
    if not (1 <= slots <= max_needed):
        await message.answer(
            f"Слишком большое или слишком маленькое число. Диапазон: 1–{max_needed}."
        )
        return

    lobby_id = await db.create_lobby(
        leader_id=message.from_user.id,
        game=data["game"],
        platform=data["platform"],
        rank=data["rank"],
        start_time=data["start_time"],
        free_slots=slots,
        max_party=int(data["max_party"]),
    )
    await state.clear()
    user = await db.get_user(message.from_user.id)
    lobby = await db.get_lobby(lobby_id)
    await message.answer("Лобби опубликовано.\n\n" + lobby_card(lobby), reply_markup=main_menu(user["role"]))


@router.message(F.text == "Открытые лобби")
async def open_lobbies(message: Message) -> None:
    user = await db.get_user(message.from_user.id)
    if user is None:
        await message.answer("Сначала /start")
        return
    rows = await db.list_open_lobbies()
    if not rows:
        await message.answer("Сейчас никто не собирает пати.", reply_markup=main_menu(user["role"]))
        return
    for row in rows:
        await message.answer(
            lobby_card(row),
            reply_markup=lobby_actions_kb(row["id"], user["role"], row["leader_id"] == user["id"]),
        )


@router.callback_query(F.data.startswith("join:"))
async def join_cb(callback: CallbackQuery) -> None:
    user = await db.get_user(callback.from_user.id)
    if user is None:
        await callback.answer("Сначала /start", show_alert=True)
        return
    lobby_id = int(callback.data.split(":")[1])
    result = await db.join_lobby(lobby_id, user["id"])
    texts = {
        "not_found": "Лобби не найдено",
        "closed": "Сбор уже закрыт",
        "leader": "Ты лидер этого лобби",
        "full": "Мест нет",
        "already": "Ты уже в этом лобби",
        "joined": "Ты в пати",
        "complete": "Ты занял последнее место. Лобби скомплектовано",
    }
    await callback.answer(texts.get(result, result), show_alert=True)
    if result in {"joined", "complete"}:
        lobby = await db.get_lobby(lobby_id)
        await callback.message.edit_text(lobby_card(lobby))


@router.message(F.text == "Пожаловаться")
async def report_start(message: Message, state: FSMContext) -> None:
    user = await db.get_user(message.from_user.id)
    if user is None:
        await message.answer("Сначала /start")
        return
    await state.set_state(ReportSG.lobby)
    await message.answer("ID лобби, на которое жалоба (число). Если без лобби — напиши 0.", reply_markup=cancel_kb())


@router.message(ReportSG.lobby)
async def report_lobby(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip()
    if not raw.isdigit():
        await message.answer("Нужен номер лобби или 0.")
        return
    lobby_id = int(raw)
    if lobby_id != 0:
        lobby = await db.get_lobby(lobby_id)
        if lobby is None:
            await message.answer("Такого лобби нет. Проверь ID.")
            return
    await state.update_data(lobby_id=None if lobby_id == 0 else lobby_id)
    await state.set_state(ReportSG.reason)
    await message.answer("Опиши токсичность коротко (5–240 символов).")


@router.message(ReportSG.reason)
async def report_reason(message: Message, state: FSMContext) -> None:
    reason = (message.text or "").strip()
    if not (5 <= len(reason) <= 240):
        await message.answer("Текст жалобы: 5–240 символов.")
        return
    data = await state.get_data()
    await db.add_report(message.from_user.id, data.get("lobby_id"), reason)
    await state.clear()
    user = await db.get_user(message.from_user.id)
    await message.answer("Жалоба ушла кураторам.", reply_markup=main_menu(user["role"]))
