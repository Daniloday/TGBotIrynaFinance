import re

from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from app.db import SQLiteRepo
from app.domain.errors import ParseErrorCode
from app.routers.common import require_session, username_from_message
from app.texts import MSG
from app.utils.currency import format_uah
from app.utils.parser import parse_message, ParseError

router = Router()

PARSE_ERROR_TO_TEXT = {
    ParseErrorCode.INVALID_FORMAT: MSG.PARSE_INVALID_FORMAT,
    ParseErrorCode.INVALID_AMOUNT: MSG.PARSE_BAD_AMOUNT,
    ParseErrorCode.NO_TITLE: MSG.PARSE_NO_TITLE,
    ParseErrorCode.UNKNOWN_PEOPLE: MSG.PARSE_UNKNOWN_PEOPLE,
}

_ONLY_AMOUNT_RE = re.compile(r"^-\d+(?:[.,]\d{1,2})?$")


@router.message(F.text.startswith("-"))
async def handle_expense(message: Message, repo: SQLiteRepo):
    text = (message.text or "").strip()

    if _ONLY_AMOUNT_RE.fullmatch(text):
        return

    session = await require_session(message, repo)
    if not session:
        return

    if len(session.participants) < 2:
        await message.answer(MSG.EXPENSE_NEED_TWO_PARTICIPANTS)
        return

    author = await require_username(message)
    if not author:
        return

    if not await require_participants(message, session):
        return

    try:
        expense = parse_message(
            text=message.text or "",
            author_username=author,
            session_participants=session.participants,
        )
    except ParseError as e:
        await message.answer(PARSE_ERROR_TO_TEXT.get(e.code, MSG.PARSE_INVALID_FORMAT))
        return

    eid = repo.add_expense(
        session_id=session.sid,
        payer=expense["payer"],
        amount_cents=expense["amount_cents"],
        title=expense["title"],
        participants=expense["participants"],
    )

    participants_text = "\n".join(f"• {u}" for u in expense["participants"]) if expense[
        "participants"] else MSG.EMPTY_DASH

    await message.answer(
        f"{MSG.EXPENSE_SAVED}\n"
        + MSG.EXPENSE_SAVED_DETAILS.format(
            payer=expense["payer"],
            amount=format_uah(expense["amount_cents"]),
            title=expense["title"],
            participants=participants_text,
        ),
        reply_markup=kb_delete_expense(session.sid, eid),
    )


async def require_username(message: Message) -> str | None:
    u = username_from_message(message)
    if not u:
        await message.answer(MSG.NO_USERNAME)
        return None
    return u


async def require_participants(message: Message, session) -> bool:
    if not session.participants:
        await message.answer(MSG.NO_PARTICIPANTS)
        return False
    return True


def kb_delete_expense(sid: int, eid: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=MSG.EXPENSE_DELETE_BTN, callback_data=f"del_exp:{sid}:{eid}")]
        ]
    )


@router.callback_query(F.data.startswith("del_exp:"))
async def cb_delete_expense(cb: CallbackQuery, repo: SQLiteRepo):
    if not cb.message:
        await cb.answer()
        return

    try:
        _, sid_s, eid_s = (cb.data or "").split(":", 2)
        sid = int(sid_s)
        eid = int(eid_s)
    except Exception:
        await cb.answer(MSG.EXPENSE_DELETE_BAD_DATA, show_alert=True)
        return

    current = repo.load_session(cb.message.chat.id)
    if not current or current.sid != sid:
        await cb.answer(MSG.SESSION_DELETE_NOT_ACTUAL, show_alert=True)
        return

    ok = repo.delete_expense(expense_id=eid, session_id=sid)
    if not ok:
        await cb.answer(MSG.EXPENSE_DELETE_ERROR, show_alert=True)
        return

    await cb.message.edit_text(MSG.EXPENSE_DELETED)
    await cb.answer()

