from aiogram import Dispatcher

from handlers import admin, common, curator, gamer


def setup_routers(dp: Dispatcher) -> None:
    dp.include_router(common.router)
    dp.include_router(gamer.router)
    dp.include_router(curator.router)
    dp.include_router(admin.router)

