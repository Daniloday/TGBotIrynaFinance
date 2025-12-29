from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from app.db import SQLiteRepo

from .keyboards import (
    CB_HIST_FROM_CHECK,
    CB_DETAILS_FROM_CHECK,
    CB_BACK_CHECK,
    CB_CALC_FROM_BALANCE,
)
from .render import render_check, render_balance_plain
from .callbacks import (
    nav_hist_from_check,
    nav_details_from_check,
    nav_back_check,
    nav_calc_from_balance,
)
from ..common import reject_private

router = Router()


@router.message(Command("balance"))
async def cmd_balance(message: Message, repo: SQLiteRepo):
    if await reject_private(message):
        return
    await render_balance_plain(message, repo)


@router.message(Command("check"))
async def cmd_check(message: Message, repo: SQLiteRepo):
    if await reject_private(message):
        return
    await render_check(message, repo)


@router.callback_query(F.data == CB_HIST_FROM_CHECK)
async def cb_nav_hist_from_check(cb: CallbackQuery, repo: SQLiteRepo):
    await nav_hist_from_check(cb, repo)


@router.callback_query(F.data == CB_DETAILS_FROM_CHECK)
async def cb_nav_details_from_check(cb: CallbackQuery, repo: SQLiteRepo):
    await nav_details_from_check(cb, repo)


@router.callback_query(F.data == CB_BACK_CHECK)
async def cb_nav_back_check(cb: CallbackQuery, repo: SQLiteRepo):
    await nav_back_check(cb, repo)


@router.callback_query(F.data == CB_CALC_FROM_BALANCE)
async def cb_nav_calc_from_balance(cb: CallbackQuery, repo: SQLiteRepo):
    await nav_calc_from_balance(cb, repo)
