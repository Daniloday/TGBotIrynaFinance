from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.db import SQLiteRepo

router = Router()


def get_session(message: Message, repo: SQLiteRepo):
    session = repo.load_session(message.chat.id)
    if not session:
        return None
    return session


@router.message(Command("members"))
async def cmd_members(message: Message, repo: SQLiteRepo):
    session = get_session(message, repo)
    if not session:
        await message.answer("❗ Сесію не створено. Використай /new")
        return

    users = session.participants
    if not users:
        await message.answer("Поки що немає учасників. Додай через /add @username")
        return

    await message.answer("Учасники:\n" + "\n".join(f"• {u}" for u in users))


@router.message(Command("add"))
async def cmd_add(message: Message, repo: SQLiteRepo):
    session = get_session(message, repo)
    if not session:
        await message.answer("❗ Спочатку створи сесію через /new")
        return

    parts = (message.text or "").split()
    mentions = [p.strip() for p in parts[1:] if p.startswith("@") and len(p) > 1]

    if not mentions:
        await message.answer("Формат: /add @username @username2")
        return

    for u in mentions:
        repo.add_participant(session.sid, u)

    await message.answer("✅ Додала: " + ", ".join(mentions))


@router.message(Command("remove"))
async def cmd_remove(message: Message, repo: SQLiteRepo):
    session = get_session(message, repo)
    if not session:
        await message.answer("❗ Спочатку створи сесію через /new")
        return

    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer("Формат: /remove @username")
        return

    username = parts[1].strip()
    ok = repo.remove_participant(session.sid, username)
    if not ok:
        await message.answer("❗ Не можу видалити: цей учасник вже фігурує у витратах")
        return

    await message.answer(f"✅ Видалила {username}")
