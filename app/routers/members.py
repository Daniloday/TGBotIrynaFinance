from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.db import SQLiteRepo
from app.texts import MSG
from app.routers.common import require_session, reject_private

router = Router()


@router.message(Command("members"))
async def cmd_members(message: Message, repo: SQLiteRepo):
    if await reject_private(message):
        return
    session = await require_session(message, repo)
    if not session:
        return

    users = session.participants
    if not users:
        await message.answer(MSG.MEMBERS_EMPTY_ADD)
        return

    await message.answer(MSG.MEMBERS_TITLE.format(name=session.name, users="\n".join(f"• {u}" for u in users)))


@router.message(Command("add"))
async def cmd_add(message: Message, repo: SQLiteRepo):
    if await reject_private(message):
        return
    session = await require_session(message, repo)
    if not session:
        return

    parts = (message.text or "").split()
    mentions = [p.strip() for p in parts[1:] if p.startswith("@") and len(p) > 1]

    if not mentions:
        await message.answer(MSG.ADD_FORMAT)
        return

    added: list[str] = []
    already: list[str] = []

    for u in mentions:
        if repo.add_participant(session.sid, u):
            added.append(u)
        else:
            already.append(u)

    lines = []
    if added:
        lines.append(MSG.ADDED_USERS.format(users=", ".join(added)))
    if already:
        lines.append(MSG.ALREADY_USERS.format(users=", ".join(already)))

    await message.answer("\n".join(lines))


@router.message(Command("remove"))
async def cmd_remove(message: Message, repo: SQLiteRepo):
    if await reject_private(message):
        return
    session = await require_session(message, repo)
    if not session:
        return

    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer(MSG.REMOVE_FORMAT)
        return

    username = parts[1].strip()

    status = repo.remove_participant(session.sid, username)
    if status == "not_found":
        await message.answer(MSG.REMOVE_NOT_FOUND.format(user=username))
        return
    if status == "used":
        await message.answer(MSG.CANT_REMOVE_USED)
        return

    await message.answer(MSG.REMOVED_USER.format(user=username))
