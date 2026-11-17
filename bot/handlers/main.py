"""Assemble focused Telegram routers; domain logic stays in Django services."""

from aiogram import Router

from .callbacks import callback
from .callbacks import router as callback_router
from .registration import router as registration_router

router = Router()
router.include_router(registration_router)
router.include_router(callback_router)

__all__ = ["callback", "router"]
