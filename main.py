from os import listdir

from discord import Intents
from discord.ext import commands

from config import TOKEN

intents = Intents.default()
intents.message_content = True
intents.members = True


class Kusogaki(commands.AutoShardedBot):
    def __init__(self) -> None:
        super().__init__(command_prefix='kuso ', intents=intents, help_command=None)

    async def load_cogs(self):
        for file in listdir('kusogaki_bot/cogs'):
            if file.endswith('.py') and not file.startswith('__'):
                await self.load_extension(f'kusogaki_bot.cogs.{file[:-3]}')

    async def setup_hook(self):
        await self.load_cogs()

    async def on_ready(self):
        print('Logged in as ' + self.user.name)


bot = Kusogaki()
bot.run(TOKEN)
