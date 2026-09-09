from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
import database as db

manager_router = Router()


@manager_router.message(F.text == "🛠 Управление лобби")
async def manager_panel(message: Message):
    role = await db.get_user_role(message.from_user.id)
    if role not in ['manager', 'admin']:
        await message.answer("⛔ Недостаточно прав.")
        return
    await message.answer("Перейдите в «🎮 Активные лобби» — под каждым лобби доступна кнопка «❌ Закрыть лобби».")


@manager_router.callback_query(F.data.startswith("close_lobby:"))
async def close_lobby_callback(callback: CallbackQuery):
    order_id = int(callback.data.split(":")[1])
    owner_id = await db.get_order_owner(order_id)
    user_role = await db.get_user_role(callback.from_user.id)

    # Разрешаем закрытие, если это автор лобби ИЛИ менеджер/админ
    is_owner = (callback.from_user.id == owner_id)
    is_staff = (user_role in ['manager', 'admin'])

    if not (is_owner or is_staff):
        await callback.answer("⛔ Вы можете закрывать только собственные лобби!", show_alert=True)
        return

    await db.close_order(order_id)

    closed_by = "автором" if is_owner else f"модератором @{callback.from_user.username}"
    await callback.message.edit_text(
        f"❌ **Лобби #{order_id} было закрыто {closed_by}.**"
    )
    await callback.answer("Лобби успешно закрыто!")