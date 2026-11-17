import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from apps.attempts.models import Attempt

from bot.handlers.main import callback
from bot.keyboards.exam import question_keyboard


@pytest.mark.django_db(transaction=True)
def test_manipulated_callback_does_not_crash():
    from apps.accounts.models import StudentProfile

    StudentProfile.objects.create(telegram_id=321, full_name="Bot Test")
    message = SimpleNamespace(answer=AsyncMock())
    c = SimpleNamespace(
        from_user=SimpleNamespace(id=321),
        data="a:invalid:0:0:0",
        answer=AsyncMock(),
        message=message,
    )
    asyncio.run(callback(c, SimpleNamespace()))
    c.answer.assert_awaited_once()
    message.answer.assert_awaited_once()
    assert Attempt.objects.count() == 0


def test_callback_size_and_no_answer_key():
    import uuid

    a = SimpleNamespace(
        id=uuid.uuid4(), revision=123, cursor=1, navigation="sequential"
    )
    q = SimpleNamespace(position=1, correct_option=2)
    markup = question_keyboard(a, q)
    for row in markup.inline_keyboard:
        for button in row:
            assert len(button.callback_data.encode()) <= 64
    assert [b.text for b in markup.inline_keyboard[0]] == list("ABCD")
