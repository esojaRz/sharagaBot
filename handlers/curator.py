from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

import database as db
from config import ROLE_ADMIN, ROLE_CURATOR, STATUS_LABELS
from handlers.gamer import lobby_card
from keyboards import lobby_actions_kb, main_menu, reports_kb

router = Router()


def _is_staff(role: str) -> bool:
    return role in {ROLE_CURATOR, ROLE_ADMIN}


@router.message(F.text == "Модерация")
async def moderation(message: Message) -> None:
    user = await db.get_user(message.from_user.id)
    if user is None or not _is_staff(user["role"]):
        await message.answer("Только для кураторов и админов.")
        return
    rows = await db.list_all_lobbies()
    if not rows:
        await message.answer("Лобби нет.", reply_markup=main_menu(user["role"]))
        return
    await message.answer("Последние сборы. Можно закрыть или отправить в архив.")
    for row in rows[:10]:
        await message.answer(
            lobby_card(row),
            reply_markup=lobby_actions_kb(row["id"], user["role"], False),
        )


@router.callback_query(F.data.startswith("mod:"))
async def mod_lobby(callback: CallbackQuery) -> None:
    user = await db.get_user(callback.from_user.id)
    if user is None or not _is_staff(user["role"]):
        await callback.answer("Нет прав", show_alert=True)
        return
    _, action, lobby_id_s = callback.data.split(":")
    lobby_id = int(lobby_id_s)
    if action == "complete":
        await db.complete_lobby(lobby_id)
        await callback.answer("Сбор подтверждён как скомплектованный")
    elif action == "archive":
        await db.archive_lobby(lobby_id)
        await callback.answer("Лобби в архиве")
    else:
        await callback.answer("Неизвестное действие")
        return
    lobby = await db.get_lobby(lobby_id)
    if lobby:
        await callback.message.edit_text(
            lobby_card(lobby) + f"\n\nСтатус обновлён: {STATUS_LABELS.get(lobby['status'])}"
        )


@router.message(F.text == "Жалобы")
async def reports_list(message: Message) -> None:
    user = await db.get_user(message.from_user.id)
    if user is None or not _is_staff(user["role"]):
        await message.answer("Только для кураторов и админов.")
        return
    rows = await db.list_open_reports()
    if not rows:
        await message.answer("Открытых жалоб нет.", reply_markup=main_menu(user["role"]))
        return
    lines = []
    ids = []
    for row in rows:
        ids.append(row["id"])
        lobby_part = f"лобби #{row['lobby_id']}" if row["lobby_id"] else "без лобби"
        lines.append(f"#{row['id']} от {row['reporter_nick']} ({lobby_part}): {row['reason']}")
    await message.answer("\n\n".join(lines), reply_markup=reports_kb(ids))


@router.callback_query(F.data.startswith("report:close:"))
async def close_report(callback: CallbackQuery) -> None:
    user = await db.get_user(callback.from_user.id)
    if user is None or not _is_staff(user["role"]):
        await callback.answer("Нет прав", show_alert=True)
        return
    report_id = int(callback.data.split(":")[2])
    await db.close_report(report_id)
    await callback.answer("Жалоба закрыта")
    await callback.message.edit_text(callback.message.text + f"\n\n#{report_id} закрыта.")
