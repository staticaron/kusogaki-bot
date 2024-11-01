from discord.ext import commands

from config import AWAIZ_USER_ID
from kusogaki_bot.services.food_counter_service import FoodCounterService


class AwaizFoodCounter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.service = FoodCounterService()

    @commands.command(name='awaiz', aliases=['caseoh'])
    async def food_mention(self, ctx):
        """Increment food mention counter for Awaiz"""
        awaiz = await self.bot.fetch_user(AWAIZ_USER_ID)
        if not awaiz:
            return

        count = self.service.increment_counter(AWAIZ_USER_ID)
        embed, file = await self.service.create_mention_embed(awaiz.mention, count)
        await ctx.send(file=file, embed=embed)

    @commands.command(name='awaizcount', aliases=['drywall'])
    async def food_count(self, ctx):
        """Display food mention count for Awaiz"""
        awaiz = await self.bot.fetch_user(AWAIZ_USER_ID)
        if not awaiz:
            return

        count = self.service.get_count(AWAIZ_USER_ID)
        embed, file = await self.service.create_count_embed(awaiz.mention, count)
        await ctx.send(file=file, embed=embed)


async def setup(bot):
    await bot.add_cog(AwaizFoodCounter(bot))
