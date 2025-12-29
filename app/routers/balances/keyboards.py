from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.texts import MSG

CB_HIST_FROM_CHECK = "nav:hist_from_check"
CB_DETAILS_FROM_CHECK = "nav:details_from_check"
CB_BACK_CHECK = "nav:back_check"
CB_CALC_FROM_BALANCE = "nav:calc_from_balance"


def check_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=MSG.CHECK_BTN_HISTORY, callback_data=CB_HIST_FROM_CHECK),
                InlineKeyboardButton(text=MSG.CHECK_BTN_DETAILS, callback_data=CB_DETAILS_FROM_CHECK),
            ]
        ]
    )


def back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=MSG.BTN_BACK, callback_data=CB_BACK_CHECK)]]
    )


def balance_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=MSG.BTN_CALCULATE, callback_data=CB_CALC_FROM_BALANCE)]]
    )
