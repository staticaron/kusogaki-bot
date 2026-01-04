import os

import discord
from discord import Interaction, app_commands
from discord.ext import commands

from kusogaki_bot.core import BaseCog, KusogakiBot
from kusogaki_bot.features.aniwrap.data import MiniWrapMainView
from kusogaki_bot.features.aniwrap.service import AniWrapService
from kusogaki_bot.features.aniwrap.task_manager import TaskManager
from kusogaki_bot.shared.services.logger import logger
from kusogaki_bot.shared.utils.embeds import EmbedType, get_embed


class WrapRequest:
    def __init__(self, token, user, wt) -> None:
        self.token = token
        self.user = user
        self.wt = wt


class AniWrapCog(BaseCog):
    def __init__(self, bot: KusogakiBot):
        super().__init__(bot)
        self.bot = bot
        self.task_manager = TaskManager(bot)
        self.service = AniWrapService()

    async def cog_unload(self):
        self.task_manager.process_wraps.cancel()

    @commands.has_permissions(administrator=True)
    @commands.hybrid_command(
        name='dummywrap',
        aliases=['dw'],
        description='Generate a dummy wrap without making API calls to kusogaki',
    )
    async def send_dummy_wrap(self, ctx: commands.Context, username: str):
        """
        Send a Dummy Wrap without making a call to API
        Doesn't hit kusogaki api
        Doesn't hit anilist api
        Just for Image Generation Testing
        """

        await ctx.typing()

        response = await self.service.generate(username, 'd')

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

    @app_commands.command(name='miniwrap', description='Generate a mini wrap!')
    async def miniwrap(self, interaction: Interaction) -> None:
        """
        Send a View that will receive the style and token info using Modals sent after the view
        """

        async def submit_callback(interaction: Interaction, style, token: str):
            """
            Callback called by the modal when the token is received
            Adds the user to the wrap generation queue
            """

            await self.task_manager.wrap_queue.put(
                WrapRequest(token, interaction.user, style)
            )
            logger.info(style)

            # Start Processing Wraps if the task is inactive
            if not self.task_manager.process_wraps.is_running():
                self.task_manager.process_wraps.start()

        view = MiniWrapMainView(submit_callback)
        embd, _ = await get_embed(
            EmbedType.NORMAL,
            'Pick Design',
            '[click here](https://anilist.co/api/v2/oauth/authorize?client_id=8704&response_type=token) to get your anilist token!',
        )

        await interaction.response.send_message(
            embed=embd,
            view=view,
            ephemeral=True,
        )

    @commands.has_permissions(administrator=True)
    @app_commands.command(
        name='start_wrap_task', description='Starts the wrap processing task'
    )
    async def start_wrap_task(self, interaction: Interaction) -> None:
        """Restart the wrap processing task"""

        self.task_manager.process_wraps.start()


async def setup(bot: commands.Bot):
    await bot.add_cog(AniWrapCog(bot))
