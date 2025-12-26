from datetime import datetime

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.db import SQLiteRepo
from app.utils.tg import username_from_message

router = Router()


def default_session_name() -> str:
    return datetime.now().strftime("Сесія %d.%m %H:%M")


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
    await message.answer(
        "✅ Сесію створено\n"
        f"Назва: {name}\n"
        "Учасники:\n" + ("\n".join(f"• {u}" for u in users) if users else "—")
    )


@router.message(Command("delete"))
async def cmd_delete(message: Message, repo: SQLiteRepo):
    session = repo.load_session(message.chat.id)
    if not session:
        await message.answer("❗ Немає активної сесії")
        return

    repo.delete_chat_session(message.chat.id)
    await message.answer("🗑️ Сесію видалено. Почни нову через /new")
