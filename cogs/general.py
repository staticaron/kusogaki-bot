from discord.ext import commands

class GeneralCog(commands.Cog):
    
    bot: commands.Bot = None
    
    def __init__(self, bot:commands.Bot):
        self.bot = bot
        
    @commands.hybrid_command(name="ping", aliases=["hello"], description="Bot Latency!")
    async def ping(self, ctx: commands.Context):
        await ctx.send(f"**Latency** : {round(self.bot.latency * 1000, 2)}ms")

async def setup(bot: commands.Bot):
    await bot.add_cog(GeneralCog(bot))