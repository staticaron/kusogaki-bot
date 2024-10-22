from discord.ext import commands

from utils import gta

class GTACog(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_group(name="gta", description="Commands related to gta")
    async def gta(self, ctx: commands.Context):
        if len(ctx.subcommand_passed) <= 0:
            await ctx.send("Please provide a valid sub command")
            
    @gta.command(name="leaderboard", description="The GTA Leaderboard")
    async def leaderboard(self, ctx: commands.Context):
        reply = await gta.get_gta_leaderboard()
        
        await ctx.send(embed=reply.pages[0], view=reply)
        
async def setup(bot: commands.Bot):
    await bot.add_cog(GTACog(bot))