from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from app.texts import MSG, START_TEXT, HELP_TEXT

router = Router()


@router.message(Command("start"))
async def cmd_members(message: Message):
    await message.answer(START_TEXT)


@router.message(Command("help"))
async def cmd_members(message: Message):
    await message.answer(HELP_TEXT)
