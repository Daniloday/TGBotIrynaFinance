from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from app.db import SQLiteRepo
from app.domain.errors import ParseError, ParseErrorCode
from app.routers.common import reject_private, require_session, username_from_message
from app.texts import MSG
from app.utils.currency import format_uah
from app.utils.parser import parse_transfer_message

router = Router()


TRANSFER_PARSE_ERROR_TO_TEXT = {
    ParseErrorCode.INVALID_FORMAT: MSG.TRANSFER_INVALID_FORMAT,
    ParseErrorCode.INVALID_AMOUNT: MSG.TRANSFER_INVALID_FORMAT,
    ParseErrorCode.NO_TITLE: MSG.TRANSFER_INVALID_FORMAT,
    ParseErrorCode.UNKNOWN_PEOPLE: MSG.PARSE_UNKNOWN_PEOPLE,
}


@router.message(Command("transfer"))
async def cmd_transfer(message: Message, repo: SQLiteRepo):
    if await reject_private(message):
        return

    session = await require_session(message, repo)
    if not session:
        return

    author = username_from_message(message)
    if not author:
        await message.answer(MSG.NO_USERNAME)
        return

    try:
        transfer = parse_transfer_message(
            text=message.text or "",
            author_username=author,
            session_participants=session.participants,
        )
    except ParseError as e:
        await message.answer(TRANSFER_PARSE_ERROR_TO_TEXT.get(e.code, MSG.TRANSFER_INVALID_FORMAT))
        return

    tid = repo.add_transfer(
        session_id=session.sid,
        sender=str(transfer["sender"]),
        recipient=str(transfer["recipient"]),
        amount_cents=int(transfer["amount_cents"]),
    )

    line = MSG.TRANSFER_LINE.format(
        sender=transfer["sender"],
        recipient=transfer["recipient"],
        amount=format_uah(int(transfer["amount_cents"])),
    )
    await message.answer(
        f"{MSG.TRANSFER_SAVED}\n\n{line}",
        reply_markup=kb_delete_transfer(session.sid, tid),
    )


def kb_delete_transfer(sid: int, tid: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=MSG.TRANSFER_DELETE_BTN,
                    callback_data=f"del_tr:{sid}:{tid}",
                )
            ]
        ]
    )


def kb_confirm_delete_transfer(sid: int, tid: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=MSG.TRANSFER_DELETE_BTN_YES,
                    callback_data=f"del_tr_yes:{sid}:{tid}",
                ),
                InlineKeyboardButton(
                    text=MSG.TRANSFER_DELETE_BTN_NO,
                    callback_data=f"del_tr_no:{sid}:{tid}",
                ),
            ]
        ]
    )


@router.callback_query(F.data.startswith("del_tr:"))
async def cb_delete_transfer_confirm(cb: CallbackQuery):
    if not cb.message:
        await cb.answer()
        return

    try:
        _, sid_s, tid_s = (cb.data or "").split(":", 2)
        sid = int(sid_s)
        tid = int(tid_s)
    except Exception:
        await cb.answer(MSG.TRANSFER_DELETE_BAD_DATA, show_alert=True)
        return

    await cb.message.edit_reply_markup(
        reply_markup=kb_confirm_delete_transfer(sid, tid)
    )
    await cb.answer(MSG.TRANSFER_DELETE_CONFIRM_TITLE)


@router.callback_query(F.data.startswith("del_tr_no:"))
async def cb_delete_transfer_cancel(cb: CallbackQuery):
    if not cb.message:
        await cb.answer()
        return

    try:
        _, sid_s, tid_s = (cb.data or "").split(":", 2)
        sid = int(sid_s)
        tid = int(tid_s)
    except Exception:
        await cb.answer(MSG.TRANSFER_DELETE_BAD_DATA, show_alert=True)
        return

    await cb.message.edit_reply_markup(
        reply_markup=kb_delete_transfer(sid, tid)
    )
    await cb.answer(MSG.TRANSFER_DELETE_CANCELED)


@router.callback_query(F.data.startswith("del_tr_yes:"))
async def cb_delete_transfer_apply(cb: CallbackQuery, repo: SQLiteRepo):
    if not cb.message:
        await cb.answer()
        return

    try:
        _, sid_s, tid_s = (cb.data or "").split(":", 2)
        sid = int(sid_s)
        tid = int(tid_s)
    except Exception:
        await cb.answer(MSG.TRANSFER_DELETE_BAD_DATA, show_alert=True)
        return

    current = repo.load_session(cb.message.chat.id)
    if not current or current.sid != sid:
        await cb.answer(MSG.TRANSFER_DELETE_NOT_ACTUAL, show_alert=True)
        return

    ok = repo.delete_transfer(transfer_id=tid, session_id=sid)
    if not ok:
        await cb.answer(MSG.TRANSFER_DELETE_ERROR, show_alert=True)
        return

    await cb.message.edit_text(MSG.TRANSFER_DELETED)
    await cb.answer()
