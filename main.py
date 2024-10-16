from discord.ext import commands
from discord import Intents
from discord import Message

from config import TOKEN

intents = Intents.default()
intents.message_content = True
intents.members = True

class Kusogaki(commands.AutoShardedBot):
    
    def __init__(self) -> None:
        super().__init__( command_prefix="kuso ", intents=intents, help_command=None )
        
    async def on_ready(self):
        print("Logged in as " + self.user.name)
        
    async def on_message(self, message:Message):
        if message.author.id == self.user.id:
            return
        
        await message.channel.send( f"**Latency : ** {round(self.latency * 1000, 2)}ms")
        
    @commands.hybrid_command(name="ping", aliases=["hello"], description="Bot Latency", usage="pong")
    async def ping(self, ctx: commands.Context):
        await ctx.send( f"**Latency : ** {self.latency}")
        
bot = Kusogaki()
bot.run(TOKEN)
