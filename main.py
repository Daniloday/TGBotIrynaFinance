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


def get_session_or_reply(message: Message):
    session = repo.load_session(message.chat.id)
    if not session or not session.participants:
        return None
    return session


# --------------------
# commands
# --------------------

@dp.message(Command("new"))
async def cmd_new(message: Message):
    repo.reset(message.chat.id)

    await message.answer(
        "✅ Сесію створено\n"
        f"Учасники:\n• {username_from_message(message)}"
    )


@dp.message(Command("members"))
async def cmd_members(message: Message):
    session = get_session_or_reply(message)
    if not session:
        await message.answer("❗ Сесію не створено. Використай /new")
        return

    users = repo.get_participants(message.chat.id)
    await message.answer("Учасники:\n" + "\n".join(f"• {u}" for u in users))


@dp.message(Command("balance"))
async def cmd_balance(message: Message):
    session = get_session_or_reply(message)
    if not session or not session.expenses:
        await message.answer("Ще немає витрат")
        return

    net = session.net_balances()
    text = "Баланс:\n"
    for u, v in net.items():
        text += f"{u}: {v:.2f} грн\n"

    await message.answer(text)


@dp.message(Command("calculate"))
async def cmd_calculate(message: Message):
    session = get_session_or_reply(message)
    if not session or not session.expenses:
        await message.answer("Ще немає витрат")
        return

    transfers = session.calculate_transfers()

    if not transfers:
        await message.answer("Ніхто нікому не винен ✅")
        return

    text = "💸 Хто кому скидає:\n"
    for d, c, a in transfers:
        text += f"{d} → {c}: {a:.2f} грн\n"

    await message.answer(text)


# --------------------
# expense handler
# --------------------

@dp.message(F.text.startswith("-"))
async def handle_expense(message: Message):
    session = get_session_or_reply(message)
    if not session:
        await message.answer("❗ Спочатку створи сесію через /new")
        return

    author = username_from_message(message)
    if not author:
        await message.answer("У тебе немає Telegram username 😕")
        return

    participants = repo.get_participants(message.chat.id)

    try:
        expense = parse_message(
            text=message.text,
            author_username=author,
            session_participants=participants,
        )
    except ParseError as e:
        await message.answer(str(e))
        return

    for u in expense["participants"]:
        repo.add_participant(message.chat.id, u)

    repo.add_expense(
        chat_id=message.chat.id,
        payer=expense["payer"],
        amount=expense["amount"],
        title=expense["title"],
        participants=expense["participants"],
    )

    await message.answer(
        "Записала ✅\n"
        f"{expense['payer']} — {expense['amount']:.2f} грн\n"
        f"{expense['title']}\n"
        "Учасники: " + ", ".join(expense["participants"])
    )


# --------------------
# fallback
# --------------------

@dp.message()
async def unknown(message: Message):
    await message.answer(
        "Не зрозуміла 🤔\n"
        "Спробуй:\n"
        "`/new`\n"
        "`-450 піца`",
        parse_mode="Markdown"
    )


# --------------------
# run
# --------------------

async def main():
    me = await bot.get_me()
    print(f"I AM: {me.username} {me.id}")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
