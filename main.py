from discord.ext import commands
from discord import Intents
from discord import Message
from os import listdir

from config import TOKEN

intents = Intents.default()
intents.message_content = True
intents.members = True

class Kusogaki(commands.AutoShardedBot):
    
    def __init__(self) -> None:
        super().__init__( command_prefix="kuso ", intents=intents, help_command=None )
            
    async def load_cogs(self):
        for file in listdir("cogs"):
            if file.endswith(".py"):
                await self.load_extension(f"cogs.{file[:-3]}")
        
    async def setup_hook(self):
        await self.load_cogs()
            
    async def on_ready(self):
        print("Logged in as " + self.user.name)
        
bot = Kusogaki()
bot.run(TOKEN)
