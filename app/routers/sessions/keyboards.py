from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.texts import MSG

CB_NEW_YES = "new_yes"
CB_NEW_NO = "new_no"
CB_DEL_SESS_YES = "del_sess_yes"
CB_DEL_SESS_NO = "del_sess_no"


def kb_confirm_new_session(token: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=MSG.SESSION_NEW_BTN_YES, callback_data=f"{CB_NEW_YES}:{token}")],
            [InlineKeyboardButton(text=MSG.SESSION_NEW_BTN_NO, callback_data=f"{CB_NEW_NO}:{token}")],
        ]
    )


def kb_confirm_delete_session(sid: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=MSG.SESSION_DELETE_BTN_YES, callback_data=f"{CB_DEL_SESS_YES}:{sid}")],
            [InlineKeyboardButton(text=MSG.SESSION_DELETE_BTN_NO, callback_data=f"{CB_DEL_SESS_NO}:{sid}")],
        ]
    )
