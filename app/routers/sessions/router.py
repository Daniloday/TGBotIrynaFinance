from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from app.db import SQLiteRepo
from app.routers.common import username_from_message, reject_private
from app.state import pending
from app.texts import MSG

from .parse import parse_new_args
from .render import build_session_created_text
from .keyboards import (
    kb_confirm_new_session,
    kb_confirm_delete_session,
    CB_NEW_YES,
    CB_NEW_NO,
    CB_DEL_SESS_YES,
    CB_DEL_SESS_NO,
)
from .service import create_new_session_db

router = Router()


@router.message(Command("new"))
async def cmd_new(message: Message, repo: SQLiteRepo):
    if await reject_private(message):
        return
    current = repo.load_session(message.chat.id)

    name, mentions = parse_new_args(message.text or "/new")
    creator = username_from_message(message)

    if not current:
        _, final_name, users = create_new_session_db(
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


@router.callback_query(F.data.startswith(f"{CB_NEW_YES}:"))
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

    _, final_name, users = create_new_session_db(
        repo=repo,
        chat_id=cb.message.chat.id,
        name=data.get("name"),
        mentions=data.get("mentions", []),
        creator=data.get("creator"),
    )

    await cb.message.edit_text(build_session_created_text(final_name, users))
    await cb.answer()


@router.callback_query(F.data.startswith(f"{CB_NEW_NO}:"))
async def cb_new_no(cb: CallbackQuery):
    if cb.message:
        await cb.message.edit_text(MSG.SESSION_NEW_CANCELED)
    await cb.answer()


@router.message(Command("delete"))
async def cmd_delete(message: Message, repo: SQLiteRepo):
    if await reject_private(message):
        return
    session = repo.load_session(message.chat.id)
    if not session:
        await message.answer(MSG.NO_SESSION)
        return

    text = (
        f"{MSG.SESSION_DELETE_CONFIRM_TITLE}\n"
        + MSG.SESSION_DELETE_CONFIRM_NAME.format(name=session.name)
    )

    await message.answer(text, reply_markup=kb_confirm_delete_session(session.sid))


@router.callback_query(F.data.startswith(f"{CB_DEL_SESS_YES}:"))
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


@router.callback_query(F.data.startswith(f"{CB_DEL_SESS_NO}:"))
async def cb_delete_session_no(cb: CallbackQuery):
    if cb.message:
        await cb.message.edit_text(MSG.SESSION_DELETE_CANCELED)
    await cb.answer()
