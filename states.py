from aiogram.fsm.state import State, StatesGroup

class ProfileForm(StatesGroup):
    game = State()
    rank = State()
    hours = State()
    prime_time = State()

class CreateLobbyForm(StatesGroup):
    game = State()
    target_rank = State()
    slots = State()
    description = State()

class AdminRoleForm(StatesGroup):
    target_user_id = State()
    new_role = State()