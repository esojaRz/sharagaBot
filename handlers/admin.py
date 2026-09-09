from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from states import AdminRoleForm
import database as db
import keyboards as kb

admin_router = Router()


@admin_router.message(F.text == "👑 Назначить роль")
async def set_role_start(message: Message, state: FSMContext):
    role = await db.get_user_role(message.from_user.id)
    if role != 'admin':
        await message.answer("⛔ Доступ разрешен только Администраторам.")
        return

    await state.set_state(AdminRoleForm.target_user_id)
    await message.answer("Введите Telegram User ID пользователя:")


@admin_router.message(AdminRoleForm.target_user_id)
async def process_target_id(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("⚠️ User ID должен состоять из цифр:")
        return

    await state.update_data(target_user_id=int(message.text))
    await state.set_state(AdminRoleForm.new_role)

    await message.answer(
        f"Выберите новую роль для ID `{message.text}`:",
        reply_markup=kb.get_roles_kb()
    )


@admin_router.callback_query(AdminRoleForm.new_role, F.data.startswith("set_role:"))
async def process_new_role_callback(callback: CallbackQuery, state: FSMContext):
    new_role = callback.data.split(":")[1]
    data = await state.get_data()

    await db.set_user_role(data['target_user_id'], new_role)
    await state.clear()

    await callback.message.edit_text(
        f"✅ Пользователю `{data['target_user_id']}` успешно присвоена роль **{new_role}**!"
    )
    await callback.answer()