from discord.ext import commands
from kusogaki_bot.core import BaseCog, KusogakiBot

class MikuCog(BaseCog):
    """
    Cog that satisfies the miku needs of the deprived individual
    """
    def __init__(self, bot: KusogakiBot):
        super().__init__(bot)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
            
        if "miku" in message.content.lower():
            await message.channel.send("I'm thinking miku miku oo ee oo")

async def setup(bot: KusogakiBot):
    await bot.add_cog(MikuCog(bot))