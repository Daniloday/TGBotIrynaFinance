from aiogram import Router, F
from aiogram.types import Message

from app.db import SQLiteRepo
from app.utils.curreny import format_uah
from app.utils.parser import parse_message, ParseError
from app.utils.tg import username_from_message

router = Router()


@router.message(F.text.startswith("-"))
async def handle_expense(message: Message, repo: SQLiteRepo):
    session = repo.load_session(message.chat.id)
    if not session:
        await message.answer("❗ Спочатку створи сесію через /new")
        return

    author = username_from_message(message)
    if not author:
        await message.answer("У тебе немає Telegram username 😕")
        return

    if not session.participants:
        await message.answer("❗ У сесії немає учасників. Додай людей через /add @username")
        return

    try:
        expense = parse_message(
            text=message.text or "",
            author_username=author,
            session_participants=session.participants,
        )
    except ParseError as e:
        await message.answer(str(e))
        return

    repo.add_expense(
        session_id=session.sid,
        payer=expense["payer"],
        amount_cents=expense["amount_cents"],
        title=expense["title"],
        participants=expense["participants"],
    )

    await message.answer(
        "Записала ✅\n"
        f"{expense['payer']} — {format_uah(expense['amount_cents'])}\n"
        f"{expense['title']}\n"
        "Учасники: " + ", ".join(expense["participants"])
    )
