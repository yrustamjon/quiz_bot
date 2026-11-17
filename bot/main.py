import asyncio
import logging
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import BotCommand
from django.conf import settings

from bot.handlers.main import router


async def main():
    if not settings.TELEGRAM_BOT_TOKEN:
        raise RuntimeError("Set TELEGRAM_BOT_TOKEN securely.")
    storage = RedisStorage.from_url(settings.REDIS_URL)
    await storage.redis.ping()
    bot = Bot(
        settings.TELEGRAM_BOT_TOKEN,
        session=AiohttpSession(proxy=os.getenv("HTTPS_PROXY") or None),
    )
    dispatcher = Dispatcher(storage=storage)
    dispatcher.include_router(router)
    await bot.set_my_commands(
        [
            BotCommand(command=c, description=d)
            for c, d in [
                ("start", "Boshlash"),
                ("menu", "Bosh menyu"),
                ("help", "Yordam"),
                ("continue", "Testni davom ettirish"),
                ("cancel", "Suhbat amalini bekor qilish"),
            ]
        ]
    )
    try:
        await dispatcher.start_polling(bot)
    finally:
        await storage.close()
        await bot.session.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
