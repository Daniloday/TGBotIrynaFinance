import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message
from dotenv import load_dotenv

from app.db import SQLiteRepo
from app.parser import parse_message, ParseError

# --------------------
# bootstrap
# --------------------

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_PATH = os.getenv("DB_PATH", "data/iryna.db")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN not set")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

repo = SQLiteRepo(DB_PATH)
repo.init()


# --------------------
# helpers
# --------------------

def username_from_message(message: Message) -> str | None:
    if message.from_user and message.from_user.username:
        return f"@{message.from_user.username}"
    return None


def get_session(message: Message):
    session = repo.load_session(message.chat.id)
    if not session or not session.participants:
        return None
    return session


def format_uah(cents: int) -> str:
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}{cents // 100}.{cents % 100:02d} грн"


# --------------------
# commands
# --------------------

@dp.message(Command("new"))
async def cmd_new(message: Message):
    repo.delete_chat_session(message.chat.id)
    #TODO parse session name or create + parse users from message
    sid = repo.create_session(message.chat.id, "Test")

    u = username_from_message(message)

    if u:
        repo.add_participant(sid, u)

    await message.answer(
        "✅ Сесію створено\n"
        f"Учасники:\n• {u}"
    )


@dp.message(Command("members"))
async def cmd_members(message: Message):
    session = get_session(message)
    if not session:
        await message.answer("❗ Сесію не створено. Використай /new")
        return

    users = session.participants
    await message.answer("Учасники:\n" + "\n".join(f"• {u}" for u in users))


@dp.message(Command("balance"))
async def cmd_balance(message: Message):
    session = get_session(message)
    if not session or not session.expenses:
        await message.answer("Ще немає витрат")
        return

    net = session.net_balances_cents()
    text = "Баланс:\n"
    for u, v in net.items():
        text += f"{u}: {format_uah(v)}\n"

    await message.answer(text)


@dp.message(Command("calculate"))
async def cmd_calculate(message: Message):
    session = get_session(message)
    if not session or not session.expenses:
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


# --------------------
# expense handler
# --------------------

@dp.message(F.text.startswith("-"))
async def handle_expense(message: Message):
    session = get_session(message)
    if not session:
        await message.answer("❗ Спочатку створи сесію через /new")
        return

    author = username_from_message(message)
    if not author:
        await message.answer("У тебе немає Telegram username 😕")
        return

    participants = session.participants

    try:
        expense = parse_message(
            text=message.text,
            author_username=author,
            session_participants=participants,
        )
    except ParseError as e:
        await message.answer(str(e))
        return

    repo.add_expense(
        session_id=session.sid,
        payer=expense["payer"],
        amount_cents=expense["amount_cents"],
        title=expense["title"],
        participants=expense["participants"],
    )

    await message.answer(
        "Записала ✅\n"
        f"{expense['payer']} — {format_uah(expense['amount_cents'])}\n"
        f"{expense['title']}\n"
        "Учасники: " + ", ".join(expense["participants"])
    )


@dp.message(Command("add"))
async def cmd_add(message: Message):
    session = get_session(message)
    if not session:
        await message.answer("❗ Спочатку створи сесію через /new")
        return

    if not message.text:
        return
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Формат: /add @username")
        return

    username = parts[1].strip()
    if not username.startswith("@"):
        await message.answer("Тільки через @. Формат: /add @username")
        return

    repo.add_participant(session.sid, username)
    await message.answer(f"✅ Додала {username}")


@dp.message(Command("remove"))
async def cmd_remove(message: Message):
    session = get_session(message)
    if not session:
        await message.answer("❗ Спочатку створи сесію через /new")
        return

    if not message.text:
        return
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Формат: /remove @username")
        return

    username = parts[1].strip()
    repo.remove_participant(session.sid, username)
    await message.answer(f"✅ Видалила {username}")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
