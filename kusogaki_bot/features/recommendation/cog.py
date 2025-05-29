from typing import Optional

from discord.ext import commands

from kusogaki_bot.core import BaseCog, KusogakiBot
from kusogaki_bot.features.recommendation.service import RecommendationService


class RecommendationCog(BaseCog):
    def __init__(self, bot: KusogakiBot):
        super().__init__(bot)
        self.recommendation_service = RecommendationService()

    @commands.command(
        name='recommend', description='Have the bot recommend a manga/anime.', aliases=['rec']
    )
    async def recommend(
        self,
        ctx: commands.Context,
        anilist_username: str,
        genre: Optional[str] = '',
        media_type: Optional[str] = 'anime',
    ):
        await ctx.defer()
        await ctx.send(
            content=await self.recommendation_service.get_recommendation(
                anilist_username=anilist_username,
                media_type=media_type.lower(),
                requested_genre=genre.lower(),
                force_update=False,
            )
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(RecommendationCog(bot))
