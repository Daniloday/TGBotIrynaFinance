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


def auto_add_participant(message: Message):
    username = username_from_message(message)
    if username:
        repo.add_participant(message.chat.id, username)

# --------------------
# commands
# --------------------

@dp.message(Command("start"))
async def cmd_start(message: Message):
    auto_add_participant(message)
    await message.answer(
        "Привіт 👋\n"
        "Я *Ірина* — рахую спільні витрати.\n\n"
        "Формат:\n"
        "`-450 піца`\n"
        "`-120 таксі @ivan @anna`\n\n"
        "Команди:\n"
        "/members\n"
        "/reset\n"
        "/balance",
        parse_mode="Markdown"
    )


@dp.message(Command("members"))
async def cmd_members(message: Message):
    auto_add_participant(message)
    users = repo.get_participants(message.chat.id)

    if not users:
        await message.answer("Поки що нікого немає.")
        return

    text = "Учасники:\n" + "\n".join(f"- {u}" for u in users)
    await message.answer(text)


@dp.message(Command("reset"))
async def cmd_reset(message: Message):
    repo.reset(message.chat.id)
    auto_add_participant(message)
    await message.answer("Готово. Все стерла, починаємо з нуля ✅")


@dp.message(Command("balance"))
async def cmd_balance(message: Message):
    expenses = repo.list_expenses(message.chat.id)

    if not expenses:
        await message.answer("Ще немає витрат. Напиши щось типу: `-450 піца`", parse_mode="Markdown")
        return

    balance: dict[str, float] = {}

    for e in expenses:
        payer = e["payer"]
        amount = e["amount"]
        parts = e["participants"]

        balance[payer] = balance.get(payer, 0) + amount

        split = amount / len(parts)
        for p in parts:
            balance[p] = balance.get(p, 0) - split

    text = "Баланс:\n"
    for u, v in sorted(balance.items()):
        text += f"{u}: {v:.2f} грн\n"

    await message.answer(text)

# --------------------
# expense handler
# --------------------

@dp.message(F.text.startswith("-"))
async def handle_expense(message: Message):
    auto_add_participant(message)

    author = username_from_message(message)
    if not author:
        await message.answer("У тебе немає username 😕")
        return

    participants = repo.get_participants(message.chat.id)

    try:
        expense = parse_message(
            text=message.text,
            author_username=author,
            session_participants=set(participants),
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
    auto_add_participant(message)
    await message.answer(
        "Не зрозуміла 🤔\n"
        "Спробуй:\n"
        "`-450 піца`\n"
        "`-120 таксі @ivan`",
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
