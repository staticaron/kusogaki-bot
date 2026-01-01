import logging
import os
import pdb

import discord
from discord import app_commands
from discord.ext import commands

from kusogaki_bot.core import BaseCog, KusogakiBot
from kusogaki_bot.features.aniwrap.service import AniWrapService
from kusogaki_bot.shared.utils.embeds import EmbedType, get_embed

logger = logging.getLogger(__name__)


class AniWrapCog(BaseCog):
    service: AniWrapService = AniWrapService()

    def __init__(self, bot: KusogakiBot):
        super().__init__(bot)
        self.bot = bot
        self.service = AniWrapService()

    @app_commands.command(
        name='alwrap',
        description='Generate alwrap',
    )
    async def alwrap_slash(self, interaction: discord.Interaction, username: str):
        """Slash Command for generating AlWrap"""
        await interaction.response.defer()

        response = await self.service.generate(username)

        if response.success:
            wrap_file = discord.File(f'wraps/{username}.png')
            await interaction.response.send_message(file=wrap_file)
            logger.info(f'Wrap Generated for : {username}')

        else:
            error_embd, _ = await get_embed(
                EmbedType.ERROR, 'ERROR!', response.error_msg
            )
            await interaction.response.send_message(embed=error_embd)
            logger.error(f'ERROR OCCURRED while generating wrap for {username}')

        # Remove the saved wrap from storage
        os.remove(f'wraps/{username}.png')

    @commands.hybrid_command(name='aniwrap', aliases=['miniwrap', 'wrap', 'alwrap'], description='Generate MiniWrap')
    async def aniwrap(
        self,
        ctx: commands.Context,
        username: str,
    ):
        """Text Command for generating AlWrap"""
        await ctx.typing()

        response = await self.service.generate(username)

        if response.success:
            wrap_file = discord.File(f'wraps/{username}.png')

            await ctx.channel.send(file=wrap_file)
            logger.info(f'Wrap Generated for : {username}')

            os.remove(f'wraps/{username}.png')
        else:
            error_embd, _ = await get_embed(
                EmbedType.ERROR, 'ERROR!', response.error_msg
            )
            await ctx.channel.send(embed=error_embd)
            logger.error(f'ERROR OCCURRED while generating wrap for {username}')

    @commands.hybrid_command(name="dummywrap", aliases=["dw"], description="Generate a dummy wrap without making API calls to kusogaki")
    async def send_dummy_wrap(self, ctx: commands.Context, username: str):
        await ctx.typing()

        response = await self.service.generate(username, True)

        if response.success:
            wrap_file = discord.File(f'wraps/{username}.png')

            await ctx.channel.send(file=wrap_file)
            logger.info(f'Wrap Generated for : {username}')

            os.remove(f'wraps/{username}.png')
        else:
            error_embd, _ = await get_embed(
                EmbedType.ERROR, 'ERROR!', response.error_msg
            )
            await ctx.channel.send(embed=error_embd)
            logger.error(f'ERROR OCCURRED while generating wrap for {username}')


async def setup(bot: commands.Bot):
    await bot.add_cog(AniWrapCog(bot))
