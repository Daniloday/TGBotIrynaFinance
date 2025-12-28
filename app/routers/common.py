from typing import Union
from aiogram.types import Message, CallbackQuery

from app.db import SQLiteRepo
from app.texts import MSG

Event = Union[Message, CallbackQuery]


def chat_id_from(event: Event) -> int | None:
    if isinstance(event, Message):
        return event.chat.id
    if event.message:
        return event.message.chat.id
    return None


async def reply(event: Event, text: str, **kwargs):
    if isinstance(event, Message):
        return await event.answer(text, **kwargs)
    if event.message:
        return await event.message.answer(text, **kwargs)
    return await event.answer(text, show_alert=True)


async def require_session(event: Event, repo: SQLiteRepo):
    cid = chat_id_from(event)
    if cid is None:
        await reply(event, MSG.NO_SESSION)
        return None

    session = repo.load_session(cid)
    if not session:
        await reply(event, MSG.NO_SESSION)
        return None
    return session


def username_from_message(message: Message) -> str | None:
    u = message.from_user.username if message.from_user else None
    return f"@{u}" if u else None
