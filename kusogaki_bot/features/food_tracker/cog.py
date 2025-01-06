from discord import File
from discord.ext import commands

from config import AWAIZ_USER_ID
from kusogaki_bot.core import BaseCog, KusogakiBot
from kusogaki_bot.features.food_tracker.service import FoodCounterService
from kusogaki_bot.shared import EmbedType


class FoodCounterCog(BaseCog):
    """Cog for tracking food mentions by users"""

    def __init__(self, bot: KusogakiBot):
        super().__init__(bot)
        self.service = FoodCounterService()

    @commands.command(name='awaiz', aliases=['caseoh'])
    async def food_mention(self, ctx: commands.Context):
        """Increment food mention counter for Awaiz"""
        awaiz = await self.bot.fetch_user(AWAIZ_USER_ID)
        if not awaiz:
            return

        count = self.service.increment_counter(AWAIZ_USER_ID)
        description = f"""
            {awaiz.mention}, your caseoh is showing! Adding to the total amount of times you've mentioned food.

            **Total is now**: {count}
            """

        embed, file = await self.create_embed(
            EmbedType.NORMAL, 'Awaiz has mentioned food!', description
        )

        file = File('static/caseoh.png', filename='caseoh.png')
        embed.set_thumbnail(url='attachment://caseoh.png')

        await ctx.send(embed=embed, file=file)

    @commands.command(name='awaizcount', aliases=['drywall'])
    async def food_count(self, ctx: commands.Context):
        """Display food mention count for Awaiz"""
        awaiz = await self.bot.fetch_user(AWAIZ_USER_ID)
        if not awaiz:
            return

        count = self.service.get_count(AWAIZ_USER_ID)
        description = f"""
            He's eaten everything. {awaiz.mention} has talked about food {count} time(s). I guess he'll start eating drywall soon.
            """

        embed, file = await self.create_embed(
            EmbedType.NORMAL, 'Awaiz Food Counter', description
        )

        file = File('static/caseoh.png', filename='caseoh.png')
        embed.set_thumbnail(url='attachment://caseoh.png')

        await ctx.send(embed=embed, file=file)


async def setup(bot: KusogakiBot):
    await bot.add_cog(FoodCounterCog(bot))
