import asyncio
import logging
import os
import time

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message
from dotenv import load_dotenv

from app.db import SQLiteRepo
from app.parser import parse_message, ParseError

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_PATH = os.getenv("DB_PATH", "data/iryna.db")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

repo = SQLiteRepo(DB_PATH)
repo.init()


def username(message: Message) -> str | None:
    if message.from_user and message.from_user.username:
        return f"@{message.from_user.username}"
    return None


# ---------- commands ----------

@dp.message(Command("new"))
async def new_session(message: Message):
    owner = username(message)
    if not owner:
        await message.answer("❌ У тебе немає username")
        return

    tokens = message.text.split()
    mentions = [t for t in tokens if t.startswith("@")]
    name_parts = [t for t in tokens[1:] if not t.startswith("@")]

    if name_parts:
        name = " ".join(name_parts)
    else:
        name = time.strftime("Сесія %d березня %H:%M")

    participants = list(dict.fromkeys([owner] + mentions))

    repo.create_session(message.chat.id, name, owner, participants)

    await message.answer(
        "✅ Сесію створено\n"
        f"Назва: {name}\n"
        "Учасники:\n" + "\n".join(f"• {u}" for u in participants)
    )


@dp.message(Command("delete"))
async def delete_session(message: Message):
    if not repo.has_session(message.chat.id):
        await message.answer("Немає активної сесії.")
        return

    repo.delete_session(message.chat.id)
    await message.answer("🗑️ Сесію видалено\nСтвори нову командою /new")


@dp.message(Command("members"))
async def members(message: Message):
    if not repo.has_session(message.chat.id):
        await message.answer("❌ Спочатку створи сесію: /new")
        return

    users = repo.get_participants(message.chat.id)
    await message.answer("Учасники:\n" + "\n".join(f"- {u}" for u in users))


@dp.message(Command("calculate"))
async def calculate(message: Message):
    if not repo.has_session(message.chat.id):
        await message.answer("❌ Немає активної сесії")
        return

    session = repo.load_session(message.chat.id)
    transfers = session.calculate_transfers()

    if not transfers:
        await message.answer("Ніхто нікому не винен ✅")
        return

    text = "💸 Хто кому скидає:\n"
    for d, c, a in transfers:
        text += f"{d} → {c}: {a:.2f} грн\n"

    await message.answer(text)


# ---------- expenses ----------

@dp.message(F.text.startswith("-"))
async def expense(message: Message):
    if not repo.has_session(message.chat.id):
        await message.answer("❌ Сесія не створена\nСтвори її: /new")
        return

    author = username(message)
    if not author:
        await message.answer("❌ У тебе немає username")
        return

    session_users = repo.get_participants(message.chat.id)

    try:
        data = parse_message(
            message.text,
            author,
            session_users,
        )
    except ParseError as e:
        await message.answer(str(e))
        return

    for u in data["participants"]:
        if u not in session_users:
            await message.answer(f"❌ {u} не входить до цієї сесії")
            return

    repo.add_expense(
        message.chat.id,
        data["payer"],
        data["amount"],
        data["title"],
        data["participants"],
    )

    await message.answer(
        "Записала ✅\n"
        f"{data['payer']} — {data['amount']:.2f} грн\n"
        f"{data['title']}\n"
        f"Учасники: {', '.join(data['participants'])}"
    )


# ---------- run ----------

async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
