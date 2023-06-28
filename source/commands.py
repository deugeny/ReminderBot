import asyncio
from typing import List, Never, Iterator, Sequence

from telegram import BotCommand
from telegram.ext import ExtBot


def initialize_commands_menu(bot: ExtBot, commands: Sequence[BotCommand]) -> Never:
    if not len(commands):
        return

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(__set_commands(bot=bot, commands=commands))
    finally:
        pass

async def __set_commands(bot: ExtBot, commands: Sequence[BotCommand]) -> Never:
    await bot.set_my_commands(commands)
