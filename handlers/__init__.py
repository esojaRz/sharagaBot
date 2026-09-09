from aiogram import Router
from .user import user_router
from .manager import manager_router
from .admin import admin_router

main_router = Router()
main_router.include_routers(user_router, manager_router, admin_router)

__all__ = ["main_router"]