import os

import discord
from discord.ext import commands

from kusogaki_bot.core import BaseCog, KusogakiBot
from kusogaki_bot.features.aniwrap.service import AniWrapService


class AniWrapCog(BaseCog):
    service: AniWrapService = AniWrapService()

    def __init__(self, bot: KusogakiBot):
        super().__init__(bot)
        self.service = AniWrapService()

    @commands.command(
        name='aniwrap', aliases=['miniwrap', 'wrap'], description='Generate MiniWrap'
    )
    async def aniwrap(
        self,
        ctx: commands.Context,
        username: str,
    ):
        self.service.generate(username)
        wrap_file = discord.File(f'wraps/{username}.png')
        await ctx.channel.send('This is your Wrap', file=wrap_file)

        os.remove(f'wraps/{username}.png')


async def setup(bot: commands.Bot):
    await bot.add_cog(AniWrapCog(bot))
