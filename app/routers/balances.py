from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.db import SQLiteRepo
from app.texts import MSG
from app.utils.currency import format_uah
from app.routers.common import require_session

router = Router()


@router.message(Command("balance"))
async def cmd_balance(message: Message, repo: SQLiteRepo):
    session = await require_session(message, repo)
    if not session:
        return
    if not session.expenses:
        await message.answer(MSG.NO_EXPENSES_YET)
        return

    net = session.net_balances_cents()
    lines = "".join(f"{u}: {format_uah(v)}\n" for u, v in net.items())
    await message.answer(MSG.BALANCE_TITLE.format(lines=lines.rstrip()))


@router.message(Command("calculate"))
async def cmd_calculate(message: Message, repo: SQLiteRepo):
    session = await require_session(message, repo)
    if not session:
        return
    if not session.expenses:
        await message.answer(MSG.NO_EXPENSES_YET)
        return

    transfers = session.calculate_transfers()
    if not transfers:
        await message.answer(MSG.TRANSFERS_NONE)
        return

    lines = "".join(f"{d} → {c}: {format_uah(a)}\n" for d, c, a in transfers)
    await message.answer(MSG.TRANSFERS_TITLE.format(lines=lines.rstrip()))
