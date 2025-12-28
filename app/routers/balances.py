from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
)

from app.db import SQLiteRepo
from app.texts import MSG
from app.utils.currency import format_uah
from app.routers.common import require_session
from app.routers.history import render_history

router = Router()


def check_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=MSG.CHECK_BTN_HISTORY, callback_data="nav:hist_from_check"),
                InlineKeyboardButton(text=MSG.CHECK_BTN_DETAILS, callback_data="nav:details_from_check"),
            ]
        ]
    )


def back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=MSG.BTN_BACK, callback_data="nav:back_check")]]
    )


def balance_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=MSG.BTN_CALCULATE, callback_data="nav:calc_from_balance")]]
    )


async def render_check(message: Message | CallbackQuery, repo: SQLiteRepo):
    session = await require_session(message, repo)
    if not session:
        return
    if not session.expenses:
        await message.answer(MSG.NO_EXPENSES_YET)
        return

    transfers = session.calculate_transfers()

    if not transfers:
        text = MSG.TRANSFERS_NONE
    else:
        lines = "".join(f"{d} → {c}: {format_uah(a)}\n" for d, c, a in transfers)
        text = MSG.TRANSFERS_TITLE.format(lines=lines.rstrip())

    if isinstance(message, CallbackQuery):
        await message.message.edit_text(text, reply_markup=check_kb())
        await message.answer()
    else:
        await message.answer(text, reply_markup=check_kb())


async def render_balance_plain(message: Message | CallbackQuery, repo: SQLiteRepo):
    session = await require_session(message, repo)
    if not session:
        return
    if not session.expenses:
        await message.answer(MSG.NO_EXPENSES_YET)
        return

    text = build_balance_text(session)

    # В обычном /balance: только кнопка "Розрахувати"
    if isinstance(message, CallbackQuery):
        await message.message.edit_text(text, reply_markup=balance_kb())
        await message.answer()
    else:
        await message.answer(text, reply_markup=balance_kb())

def _fmt_lines_amount(d: dict[str, int]) -> str:
    # можно сортировать как хочешь, я бы по убыванию суммы:
    items = sorted(d.items(), key=lambda x: x[1], reverse=True)
    return "".join(f"{u}: {format_uah(v)}\n" for u, v in items).rstrip()


def build_balance_text(session) -> str:
    net = session.net_balances_cents()
    paid = session.totals_paid_cents()
    spent = session.totals_spent_cents()

    balance_block = MSG.BALANCE_BLOCK_TITLE.format(lines=_fmt_lines_amount(net))
    paid_block = MSG.BALANCE_PAID_TITLE.format(lines=_fmt_lines_amount(paid))
    spent_block = MSG.BALANCE_SPENT_TITLE.format(lines=_fmt_lines_amount(spent))

    return MSG.BALANCE_FULL.format(
        balance=balance_block,
        paid=paid_block,
        spent=spent_block,
    )


async def render_balance_from_check(cb: CallbackQuery, repo: SQLiteRepo):
    session = await require_session(cb, repo)
    if not session:
        return
    if not session.expenses:
        await cb.message.edit_text(MSG.NO_EXPENSES_YET, reply_markup=back_kb())
        await cb.answer()
        return

    text = build_balance_text(session)

    await cb.message.edit_text(text, reply_markup=back_kb())
    await cb.answer()


@router.message(Command("balance"))
async def cmd_balance(message: Message, repo: SQLiteRepo):
    await render_balance_plain(message, repo)


@router.message(Command("check"))
async def cmd_check(message: Message, repo: SQLiteRepo):
    await render_check(message, repo)


# --- callbacks ---

@router.callback_query(F.data == "nav:hist_from_check")
async def cb_nav_hist_from_check(cb: CallbackQuery, repo: SQLiteRepo):
    # открываем историю в check-контексте: другой prefix + back-кнопка на всех страницах
    await render_history(cb, repo, page=1, prefix="histc:", back_cb="nav:back_check")


@router.callback_query(F.data == "nav:details_from_check")
async def cb_nav_details_from_check(cb: CallbackQuery, repo: SQLiteRepo):
    await render_balance_from_check(cb, repo)


@router.callback_query(F.data == "nav:back_check")
async def cb_nav_back_check(cb: CallbackQuery, repo: SQLiteRepo):
    await render_check(cb, repo)


@router.callback_query(F.data == "nav:calc_from_balance")
async def cb_nav_calc_from_balance(cb: CallbackQuery, repo: SQLiteRepo):
    await render_check(cb, repo)
