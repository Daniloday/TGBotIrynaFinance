from aiogram.types import Message, CallbackQuery

from app.db import SQLiteRepo
from app.texts import MSG
from app.utils.currency import format_uah
from app.routers.common import require_session

from .keyboards import check_kb, back_kb, balance_kb


def _fmt_lines_amount(d: dict[str, int]) -> str:
    items = sorted(d.items(), key=lambda x: x[1], reverse=True)
    return "".join(f"{u}: {format_uah(v)}\n" for u, v in items).rstrip()


def _fmt_transfer_lines(transfers: dict[tuple[str, str], int]) -> str:
    items = sorted(transfers.items(), key=lambda x: (x[0][0], x[0][1]))
    return "".join(f"{sender} → {recipient}: {format_uah(amount)}\n" for (sender, recipient), amount in items).rstrip()


def build_balance_text(session) -> str:
    net = session.net_balances_cents()
    paid = session.totals_paid_cents()
    spent = session.totals_spent_cents()
    actual_transfers = session.actual_transfers_cents()

    balance_block = MSG.BALANCE_BLOCK_TITLE.format(lines=_fmt_lines_amount(net))
    paid_block = MSG.BALANCE_PAID_TITLE.format(lines=_fmt_lines_amount(paid))
    spent_block = MSG.BALANCE_SPENT_TITLE.format(lines=_fmt_lines_amount(spent))
    transfers_block = ""
    if actual_transfers:
        transfers_block = "\n\n" + MSG.BALANCE_TRANSFERS_TITLE.format(
            lines=_fmt_transfer_lines(actual_transfers)
        )

    return MSG.BALANCE_FULL.format(
        name=session.name,
        balance=balance_block,
        paid=paid_block,
        spent=spent_block,
        transfers=transfers_block,
    )


async def render_check(message: Message | CallbackQuery, repo: SQLiteRepo):
    session = await require_session(message, repo)
    if not session:
        return
    if not session.has_operations():
        await message.answer(MSG.NO_OPERATIONS)
        return

    transfers = session.calculate_transfers()

    if not transfers:
        text = MSG.TRANSFERS_NONE
    else:
        lines = "".join(f"{d} → {c}: {format_uah(a)}\n" for d, c, a in transfers)
        text = MSG.TRANSFERS_TITLE.format(name=session.name, lines=lines.rstrip())

    if isinstance(message, CallbackQuery):
        await message.message.edit_text(text, reply_markup=check_kb())
        await message.answer()
    else:
        await message.answer(text, reply_markup=check_kb())


async def render_balance_plain(message: Message | CallbackQuery, repo: SQLiteRepo):
    session = await require_session(message, repo)
    if not session:
        return
    if not session.has_operations():
        await message.answer(MSG.NO_OPERATIONS)
        return

    text = build_balance_text(session)

    if isinstance(message, CallbackQuery):
        await message.message.edit_text(text, reply_markup=balance_kb())
        await message.answer()
    else:
        await message.answer(text, reply_markup=balance_kb())


async def render_balance_from_check(cb: CallbackQuery, repo: SQLiteRepo):
    session = await require_session(cb, repo)
    if not session:
        return
    if not session.has_operations():
        await cb.message.edit_text(MSG.NO_OPERATIONS, reply_markup=back_kb())
        await cb.answer()
        return

    text = build_balance_text(session)

    await cb.message.edit_text(text, reply_markup=back_kb())
    await cb.answer()
