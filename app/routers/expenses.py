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


@router.message(F.text.startswith("-"))
async def handle_expense(message: Message, repo: SQLiteRepo):
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

    await message.answer(
        f"{MSG.EXPENSE_SAVED}\n"
        + MSG.EXPENSE_SAVED_DETAILS.format(
            payer=expense["payer"],
            amount=format_uah(expense["amount_cents"]),
            title=expense["title"],
            participants=", ".join(expense["participants"]),
        ),
        reply_markup=kb_delete_expense(eid),
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


def kb_delete_expense(eid: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=MSG.EXPENSE_DELETE_BTN, callback_data=f"del_exp:{eid}")]
        ]
    )


@router.callback_query(F.data.startswith("del_exp:"))
async def cb_delete_expense(cb: CallbackQuery, repo: SQLiteRepo):
    try:
        eid = int((cb.data or "").split(":", 1)[1])
    except Exception:
        await cb.answer(MSG.EXPENSE_DELETE_BAD_DATA, show_alert=True)
        return

    ok = repo.delete_expense(eid)
    if not ok:
        await cb.answer(MSG.EXPENSE_DELETE_ERROR, show_alert=True)
        return

    if cb.message:
        await cb.message.edit_text(MSG.EXPENSE_DELETED)

    await cb.answer()

