import logging
import os

import discord
from discord import app_commands
from discord.ext import commands

from kusogaki_bot.core import BaseCog, KusogakiBot
from kusogaki_bot.features.aniwrap.service import AniWrapService

logger = logging.getLogger(__name__)


class AniWrapCog(BaseCog):
    service: AniWrapService = AniWrapService()

    def __init__(self, bot: KusogakiBot):
        super().__init__(bot)
        self.bot = bot
        self.service = AniWrapService()

    @app_commands.guilds(discord.Object(id=954353883977748512))
    @app_commands.command(
        name='alwrap',
        description='Generate alwrap',
    )
    async def alwrap_slash(self, interaction: discord.Interaction, username: str):
        """Slash Command for generating AlWrap"""
        await interaction.response.defer()

        generation_success = await self.service.generate(username)
        wrap_file = discord.File(f'wraps/{username}.png')

        if generation_success:
            await interaction.response.send_message(
                f'{interaction.user.mention}', file=wrap_file
            )
            logger.info(f'Wrap Generated for : {username}')
        else:
            await interaction.response.send_message(
                f'ERROR OCCURRED! {interaction.user.mention}'
            )
            logger.error(f'ERROR OCCURRED while generating wrap for {username}')

        # Remove the saved wrap from storage
        os.remove(f'wraps/{username}.png')

    @commands.hybrid_command(
        name='aniwrap', aliases=['miniwrap', 'wrap'], description='Generate MiniWrap'
    )
    async def aniwrap(
        self,
        ctx: commands.Context,
        username: str,
    ):
        """Text Command for generating AlWrap"""
        await ctx.typing()

        generation_success = await self.service.generate(username)
        wrap_file = discord.File(f'wraps/{username}.png')

        if generation_success:
            await ctx.channel.send(file=wrap_file)
            logger.info(f'Wrap Generated for : {username}')
        else:
            await ctx.channel.send('ERROR OCCURRED!')
            logger.error(f'ERROR OCCURRED while generating wrap for {username}')

        # Remove the saved wrap from storage
        os.remove(f'wraps/{username}.png')


async def setup(bot: commands.Bot):
    await bot.add_cog(AniWrapCog(bot))
