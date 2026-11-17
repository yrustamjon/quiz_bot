"""Verify real Redis FSM persistence using only isolated, disposable keys."""

import asyncio
import os
import uuid
from pathlib import Path

from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.redis import DefaultKeyBuilder, RedisStorage
from dotenv import load_dotenv


async def main():
    load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=False)
    url = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
    prefix = "quiz-verification-" + uuid.uuid4().hex
    key = StorageKey(bot_id=0, chat_id=0, user_id=0)

    def storage():
        return RedisStorage.from_url(
            url, key_builder=DefaultKeyBuilder(prefix=prefix, with_bot_id=True)
        )

    first = storage()
    try:
        await first.redis.ping()
        await first.set_state(key, "Verification:ready")
        await first.set_data(key, {"step": "verification"})
    finally:
        await first.close()
    second = storage()
    try:
        assert await second.get_state(key) == "Verification:ready"
        assert await second.get_data(key) == {"step": "verification"}
        await second.set_state(key, None)
        await second.set_data(key, {})
        assert await second.get_state(key) is None
    finally:
        await second.close()
    print(
        "Redis FSM write/reconnect/read/isolated-key cleanup passed. No live keys were cleared."
    )


if __name__ == "__main__":
    asyncio.run(main())
