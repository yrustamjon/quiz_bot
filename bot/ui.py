"""Update a Telegram panel in place; fall back safely for missing/old messages."""

import asyncio
from weakref import WeakValueDictionary

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InputMediaPhoto, LinkPreviewOptions, Message, MessageEntity

_locks = WeakValueDictionary()


def panel_lock(message):
    key = (message.chat.id, message.message_id)
    lock = _locks.get(key)
    if lock is None:
        lock = asyncio.Lock()
        _locks[key] = lock
    return lock


def _markup(value):
    return value.model_dump(exclude_none=True) if value is not None else None


def _cannot_edit(error):
    return any(
        value in error.message.lower()
        for value in [
            "message to edit not found",
            "message can't be edited",
            "message_id_invalid",
            "there is no text in the message",
            "message is too old",
        ]
    )


def text_entities(text):
    heading = text.split("\n", 1)[0]
    return (
        [
            MessageEntity(
                type="bold", offset=0, length=len(heading.encode("utf-16-le")) // 2
            )
        ]
        if heading
        else []
    )


def text_chunks(text, limit=3800):
    chunk = []
    length = 0
    for char in text:
        width = 2 if ord(char) > 0xFFFF else 1
        if length + width > limit:
            yield "".join(chunk)
            chunk = []
            length = 0
        chunk.append(char)
        length += width
    if chunk:
        yield "".join(chunk)


class Panel:
    """Only the first response replaces the clicked panel; long continuations append.

    User messages are never edited. Callback handlers construct this adapter only
    for the bot message that carried the pressed inline button.
    """

    def __init__(self, message, lock=None):
        self.message = getattr(lock, "panel_message", None) or message
        self.lock = lock
        self.used = False

    def remember(self, result):
        if isinstance(result, Message):
            self.message = result
            if self.lock is not None:
                self.lock.panel_message = result
        return result

    @property
    def bot(self):
        return self.message.bot

    async def answer(self, text, **kwargs):
        first = not self.used
        self.used = True
        kwargs.setdefault("link_preview_options", LinkPreviewOptions(is_disabled=True))
        kwargs.setdefault("entities", text_entities(text))
        if first and not self.message.photo:
            if self.message.text == text and _markup(
                self.message.reply_markup
            ) == _markup(kwargs.get("reply_markup")):
                return self.message
            try:
                return self.remember(await self.message.edit_text(text, **kwargs))
            except TelegramBadRequest as error:
                if "message is not modified" in error.message.lower():
                    return self.message
                if not _cannot_edit(error):
                    raise
        # Telegram cannot turn a photo into a text-only message. Keep its history
        # and remove old controls, then send one text panel rather than deleting it.
        if first and self.message.photo:
            try:
                await self.message.edit_reply_markup(reply_markup=None)
            except TelegramBadRequest as error:
                if (
                    not _cannot_edit(error)
                    and "message is not modified" not in error.message.lower()
                ):
                    raise
        return self.remember(await self.message.answer(text, **kwargs))

    async def answer_photo(self, photo, **kwargs):
        first = not self.used
        self.used = True
        if first:
            try:
                if (
                    isinstance(photo, str)
                    and self.message.photo
                    and self.message.photo[-1].file_id == photo
                ):
                    return self.remember(
                        await self.message.edit_caption(
                            caption=kwargs.get("caption"),
                            caption_entities=text_entities(kwargs.get("caption") or ""),
                            reply_markup=kwargs.get("reply_markup"),
                        )
                    )
                return self.remember(
                    await self.message.edit_media(
                        media=InputMediaPhoto(
                            media=photo,
                            caption=kwargs.get("caption"),
                            caption_entities=text_entities(kwargs.get("caption") or ""),
                        ),
                        reply_markup=kwargs.get("reply_markup"),
                    )
                )
            except TelegramBadRequest as error:
                if "message is not modified" in error.message.lower():
                    return self.message
                if not _cannot_edit(error):
                    self.used = False
                    raise
        return self.remember(await self.message.answer_photo(photo, **kwargs))
