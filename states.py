from aiogram.fsm.state import State, StatesGroup


class RegisterSG(StatesGroup):
    nick = State()
    experience = State()
    language = State()


class LobbyCreateSG(StatesGroup):
    game = State()
    platform = State()
    rank = State()
    start_time = State()
    slots = State()


class ReportSG(StatesGroup):
    lobby = State()
    reason = State()


class AdminGameSG(StatesGroup):
    name = State()
    max_party = State()


class AdminSettingSG(StatesGroup):
    value = State()


class AdminRoleSG(StatesGroup):
    user_id = State()
    role = State()
