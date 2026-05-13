import asyncio
import logging
from aiogram import Bot, Dispatcher
from app.config import get_settings
from app.db import SQLiteRepo
from app.routers import sessions, members, expenses, balances, history, start, transfers


async def main():
    logging.basicConfig(level=logging.INFO)

    settings = get_settings()

    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher()

    repo = SQLiteRepo(settings.DB_PATH)
    repo.init()

    dp["repo"] = repo

    dp.include_router(sessions.router)
    dp.include_router(members.router)
    dp.include_router(transfers.router)
    dp.include_router(expenses.router)
    dp.include_router(balances.router)
    dp.include_router(history.router)
    dp.include_router(start.router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
