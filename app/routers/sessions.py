from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)

from app.db import SQLiteRepo
from app.routers.common import username_from_message
from app.texts import MSG, default_session_name
from app.state import pending

router = Router()


# -------------------------
# Helpers
# -------------------------

def parse_new_args(text: str) -> tuple[str | None, list[str]]:
    parts = (text or "").split()
    tokens = parts[1:]
    mentions = [t for t in tokens if t.startswith("@") and len(t) > 1]
    name_tokens = [t for t in tokens if not (t.startswith("@") and len(t) > 1)]
    name = " ".join(name_tokens).strip() or None
    return name, mentions


def build_session_created_text(name: str, users: list[str]) -> str:
    users_text = "\n".join(f"• {u}" for u in users) if users else MSG.EMPTY_DASH
    return (
        f"{MSG.SESSION_CREATED}\n\n"
        + MSG.SESSION_CREATED_NAME.format(name=name)
        + "\n\n"
        + MSG.SESSION_CREATED_USERS.format(users=users_text)
    )


def kb_confirm_new_session(token: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=MSG.SESSION_NEW_BTN_YES, callback_data=f"new_yes:{token}")],
            [InlineKeyboardButton(text=MSG.SESSION_NEW_BTN_NO, callback_data=f"new_no:{token}")],
        ]
    )


def kb_confirm_delete_session(sid: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=MSG.SESSION_DELETE_BTN_YES, callback_data=f"del_sess_yes:{sid}")],
            [InlineKeyboardButton(text=MSG.SESSION_DELETE_BTN_NO, callback_data=f"del_sess_no:{sid}")],
        ]
    )


def _create_new_session_db(
    repo: SQLiteRepo,
    chat_id: int,
    name: str | None,
    mentions: list[str],
    creator: str | None,
) -> tuple[int, str, list[str]]:
    """
    Создаёт сессию в БД и возвращает (sid, name, users).
    creator - кто должен быть добавлен как участник (автор /new).
    """
    if not name:
        name = default_session_name()

    sid = repo.create_session(chat_id, name)

    if creator:
        repo.add_participant(sid, creator)

    for u in mentions:
        repo.add_participant(sid, u)

    users = repo.list_participants(sid)
    return sid, name, users


# -------------------------
# /new
# -------------------------

@router.message(Command("new"))
async def cmd_new(message: Message, repo: SQLiteRepo):
    current = repo.load_session(message.chat.id)

    name, mentions = parse_new_args(message.text or "/new")
    creator = username_from_message(message)

    if not current:
        _, final_name, users = _create_new_session_db(
            repo=repo,
            chat_id=message.chat.id,
            name=name,
            mentions=mentions,
            creator=creator,
        )
        await message.answer(build_session_created_text(final_name, users))
        return

    token = pending.create(
        action="new_session",
        chat_id=message.chat.id,
        payload={
            "sid": current.sid,
            "name": name,
            "mentions": mentions,
            "creator": creator,
        },
    )

    await message.answer(
        f"{MSG.SESSION_NEW_CONFIRM_TITLE}\n"
        + MSG.SESSION_NEW_CONFIRM_NAME.format(name=current.name),
        reply_markup=kb_confirm_new_session(token),
    )


@router.callback_query(F.data.startswith("new_yes:"))
async def cb_new_yes(cb: CallbackQuery, repo: SQLiteRepo):
    if not cb.message:
        await cb.answer()
        return

    token = (cb.data or "").split(":", 1)[1]

    data = pending.pop(
        token,
        chat_id=cb.message.chat.id,
        action="new_session",
    )
    if not data:
        await cb.answer(MSG.SESSION_DELETE_NOT_ACTUAL, show_alert=True)
        return

    current = repo.load_session(cb.message.chat.id)
    if not current or current.sid != data.get("sid"):
        await cb.answer(MSG.SESSION_DELETE_NOT_ACTUAL, show_alert=True)
        return

    repo.delete_chat_session(cb.message.chat.id)

    _, final_name, users = _create_new_session_db(
        repo=repo,
        chat_id=cb.message.chat.id,
        name=data.get("name"),
        mentions=data.get("mentions", []),
        creator=data.get("creator"),
    )

    created_text = build_session_created_text(final_name, users)

    await cb.message.edit_text(created_text)
    await cb.answer()


@router.callback_query(F.data.startswith("new_no:"))
async def cb_new_no(cb: CallbackQuery):
    if cb.message:
        await cb.message.edit_text(MSG.SESSION_NEW_CANCELED)
    await cb.answer()


# -------------------------
# /delete
# -------------------------

@router.message(Command("delete"))
async def cmd_delete(message: Message, repo: SQLiteRepo):
    session = repo.load_session(message.chat.id)
    if not session:
        await message.answer(MSG.NO_ACTIVE_SESSION)
        return

    text = (
        f"{MSG.SESSION_DELETE_CONFIRM_TITLE}\n"
        + MSG.SESSION_DELETE_CONFIRM_NAME.format(name=session.name)
    )

    await message.answer(text, reply_markup=kb_confirm_delete_session(session.sid))


@router.callback_query(F.data.startswith("del_sess_yes:"))
async def cb_delete_session_yes(cb: CallbackQuery, repo: SQLiteRepo):
    if not cb.message:
        await cb.answer()
        return

    try:
        sid = int((cb.data or "").split(":", 1)[1])
    except Exception:
        await cb.answer(MSG.SESSION_DELETE_BAD_DATA, show_alert=True)
        return

    current = repo.load_session(cb.message.chat.id)
    if not current or current.sid != sid:
        await cb.answer(MSG.SESSION_DELETE_NOT_ACTUAL, show_alert=True)
        return

    repo.delete_chat_session(cb.message.chat.id)

    await cb.message.edit_text(MSG.SESSION_DELETED)
    await cb.answer()


@router.callback_query(F.data.startswith("del_sess_no:"))
async def cb_delete_session_no(cb: CallbackQuery):
    if cb.message:
        await cb.message.edit_text(MSG.SESSION_DELETE_CANCELED)
    await cb.answer()
