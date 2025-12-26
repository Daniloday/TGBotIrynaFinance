from aiogram.types import Message


def username_from_message(message: Message) -> str | None:
    u = message.from_user.username if message.from_user else None
    return f"@{u}" if u else None
