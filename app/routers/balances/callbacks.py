from aiogram.types import CallbackQuery

from app.db import SQLiteRepo
from app.routers.history import render_history

from .keyboards import (
    CB_BACK_CHECK,
)
from .render import render_check, render_balance_from_check


async def nav_hist_from_check(cb: CallbackQuery, repo: SQLiteRepo):
    await render_history(cb, repo, page=1, prefix="histc:", back_cb=CB_BACK_CHECK)


async def nav_details_from_check(cb: CallbackQuery, repo: SQLiteRepo):
    await render_balance_from_check(cb, repo)


async def nav_back_check(cb: CallbackQuery, repo: SQLiteRepo):
    await render_check(cb, repo)


async def nav_calc_from_balance(cb: CallbackQuery, repo: SQLiteRepo):
    await render_check(cb, repo)
