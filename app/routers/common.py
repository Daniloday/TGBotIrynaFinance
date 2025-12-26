from aiogram.types import Message

from app.db import SQLiteRepo
from app.texts import MSG


async def require_session(message: Message, repo: SQLiteRepo):
    session = repo.load_session(message.chat.id)
    if not session:
        await message.answer(MSG.NO_SESSION)
        return None
    return session


def username_from_message(message: Message) -> str | None:
    u = message.from_user.username if message.from_user else None
    return f"@{u}" if u else None
