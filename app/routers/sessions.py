from datetime import datetime

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.db import SQLiteRepo
from app.routers.common import username_from_message
from app.texts import MSG, default_session_name

router = Router()


def parse_new_args(text: str) -> tuple[str | None, list[str]]:
    parts = (text or "").split()
    tokens = parts[1:]
    mentions = [t for t in tokens if t.startswith("@") and len(t) > 1]
    name_tokens = [t for t in tokens if not (t.startswith("@") and len(t) > 1)]
    name = " ".join(name_tokens).strip() or None
    return name, mentions


@router.message(Command("new"))
async def cmd_new(message: Message, repo: SQLiteRepo):
    repo.delete_chat_session(message.chat.id)

    name, mentions = parse_new_args(message.text or "/new")
    if not name:
        name = default_session_name()

    sid = repo.create_session(message.chat.id, name)

    author = username_from_message(message)
    if author:
        repo.add_participant(sid, author)

    for u in mentions:
        repo.add_participant(sid, u)

    users = repo.list_participants(sid)
    users_text = "\n".join(f"• {u}" for u in users) if users else MSG.EMPTY_DASH

    await message.answer(
        f"{MSG.SESSION_CREATED}\n"
        + MSG.SESSION_CREATED_NAME.format(name=name)
        + "\n"
        + MSG.SESSION_CREATED_USERS.format(users=users_text)
    )


@router.message(Command("delete"))
async def cmd_delete(message: Message, repo: SQLiteRepo):
    session = repo.load_session(message.chat.id)
    if not session:
        await message.answer(MSG.NO_ACTIVE_SESSION)
        return

    repo.delete_chat_session(message.chat.id)
    await message.answer(MSG.SESSION_DELETED)
