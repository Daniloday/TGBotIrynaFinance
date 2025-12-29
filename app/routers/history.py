from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from datetime import datetime, date, timedelta

from app.db import SQLiteRepo
from app.texts import MSG
from app.utils.currency import format_uah
from app.routers.common import require_session, reject_private
from app.utils.time import date_local, TZ, fmt_time

router = Router()

PAGE_SIZE = 5


@router.message(Command("history"))
async def cmd_history(message: Message, repo: SQLiteRepo):
    if await reject_private(message):
        return
    await render_history(message, repo, page=1, prefix="hist:", back_cb=None)


def fmt_day_label(ts: int, today: date) -> str:
    d = date_local(ts)
    if d == today:
        return MSG.HISTORY_DAY_TODAY
    if d == today - timedelta(days=1):
        return MSG.HISTORY_DAY_YESTERDAY
    return MSG.HISTORY_DAY_DATE.format(date=d.strftime("%d.%m.%Y"))


async def render_history(
    message: Message | CallbackQuery,
    repo: SQLiteRepo,
    page: int,
    prefix: str = "hist:",
    back_cb: str | None = None,
):
    session = await require_session(message, repo)
    if not session:
        return

    total = repo.count_expenses(session.sid)
    if total == 0:
        await message.answer(MSG.HISTORY_EMPTY)
        return

    pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(1, min(page, pages))
    offset = (page - 1) * PAGE_SIZE

    expenses = repo.list_expenses(
        session_id=session.sid,
        limit=PAGE_SIZE,
        offset=offset,
    )

    lines = [MSG.HISTORY_TITLE.format(page=page, pages=pages), ""]

    today = datetime.now(TZ).date()
    last_day = None

    for i, e in enumerate(expenses, start=offset + 1):
        day = date_local(e["created_at"])
        if day != last_day:
            lines.append(fmt_day_label(e["created_at"], today))
            lines.append("")
            last_day = day

        lines.append(
            MSG.HISTORY_ITEM.format(
                idx=i,
                time=fmt_time(e["created_at"]),
                payer=e["payer"],
                title=e["title"],
                amount=format_uah(e["amount_cents"]),
                participants=", ".join(e["participants"]),
            )
        )
        lines.append("")

    text = "\n".join(lines).strip()
    kb = history_nav_kb(page, pages, prefix=prefix, back_cb=back_cb)

    if isinstance(message, CallbackQuery):
        await message.message.edit_text(text, reply_markup=kb)
        await message.answer()
    else:
        await message.answer(text, reply_markup=kb)


def history_nav_kb(
    page: int,
    pages: int,
    prefix: str = "hist:",
    back_cb: str | None = None,
) -> InlineKeyboardMarkup | None:
    rows: list[list[InlineKeyboardButton]] = []

    nav: list[InlineKeyboardButton] = []
    if page > 1:
        nav.append(InlineKeyboardButton(text=MSG.HISTORY_PREV, callback_data=f"{prefix}{page - 1}"))
    if page < pages:
        nav.append(InlineKeyboardButton(text=MSG.HISTORY_NEXT, callback_data=f"{prefix}{page + 1}"))
    if nav:
        rows.append(nav)

    if back_cb:
        rows.append([InlineKeyboardButton(text=MSG.BTN_BACK, callback_data=back_cb)])

    if not rows:
        return None

    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.callback_query(F.data.startswith("hist:"))
async def cb_history(cb: CallbackQuery, repo: SQLiteRepo):
    try:
        page = int(cb.data.split(":", 1)[1])
    except Exception:
        await cb.answer()
        return
    await render_history(cb, repo, page, prefix="hist:", back_cb=None)


@router.callback_query(F.data.startswith("histc:"))
async def cb_history_from_check(cb: CallbackQuery, repo: SQLiteRepo):
    try:
        page = int(cb.data.split(":", 1)[1])
    except Exception:
        await cb.answer()
        return
    await render_history(cb, repo, page, prefix="histc:", back_cb="nav:back_check")
