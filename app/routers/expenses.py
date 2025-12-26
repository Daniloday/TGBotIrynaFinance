from aiogram import Router, F
from aiogram.types import Message

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

    repo.add_expense(
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
        )
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
