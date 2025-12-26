from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.db import SQLiteRepo
from app.utils.curreny import format_uah

router = Router()


@router.message(Command("balance"))
async def cmd_balance(message: Message, repo: SQLiteRepo):
    session = repo.load_session(message.chat.id)
    if not session:
        await message.answer("❗ Спочатку створи сесію через /new")
        return
    if not session.expenses:
        await message.answer("Ще немає витрат")
        return

    net = session.net_balances_cents()
    text = "Баланс:\n"
    for u, v in net.items():
        text += f"{u}: {format_uah(v)}\n"

    await message.answer(text)


@router.message(Command("calculate"))
async def cmd_calculate(message: Message, repo: SQLiteRepo):
    session = repo.load_session(message.chat.id)
    if not session:
        await message.answer("❗ Спочатку створи сесію через /new")
        return
    if not session.expenses:
        await message.answer("Ще немає витрат")
        return

    transfers = session.calculate_transfers()
    if not transfers:
        await message.answer("Ніхто нікому не винен ✅")
        return

    text = "💸 Хто кому скидає:\n"
    for d, c, a in transfers:
        text += f"{d} → {c}: {format_uah(a)}\n"

    await message.answer(text)
