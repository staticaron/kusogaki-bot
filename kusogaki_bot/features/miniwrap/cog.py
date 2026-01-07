import pdb
from discord import Interaction, app_commands
from discord.ext import commands

from kusogaki_bot.core import BaseCog, KusogakiBot
from kusogaki_bot.features.miniwrap.data import (
    GenerateMiniwrapView,
    EditTopMiniwrapView,
)
from kusogaki_bot.features.miniwrap.service import AniWrapService
from kusogaki_bot.features.miniwrap.task_manager import TaskManager
from kusogaki_bot.shared.services.logger import logger
from kusogaki_bot.shared.utils.embeds import EmbedType, get_embed


@app_commands.guild_only()
class MiniWrapGroup(app_commands.Group):
    pass


class WrapRequest:
    def __init__(self, token, user, wt) -> None:
        self.token = token
        self.user = user
        self.wt = wt


class AniWrapCog(BaseCog):
    miniwrapgroup = MiniWrapGroup(name='miniwrap')

    def __init__(self, bot: KusogakiBot):
        super().__init__(bot)
        self.bot = bot
        self.task_manager = TaskManager(bot)
        self.service = AniWrapService()

    async def cog_unload(self):
        self.task_manager.process_wraps.cancel()

    @miniwrapgroup.command(name='generate', description='Generate a Mini Wrap')
    async def miniwrap_generate(self, interaction: Interaction) -> None:
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

            await interaction.followup.send('You will receive your wrap in DMS soon')

        view = GenerateMiniwrapView(submit_callback)
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
    @miniwrapgroup.command(
        name='start_wrap_task', description='Starts the wrap processing task'
    )
    async def miniwrap_start_task(self, interaction: Interaction) -> None:
        """Restart the wrap processing task"""

        self.task_manager.process_wraps.start()

    @miniwrapgroup.command(
        name='edittop', description='Edit the TOP Anime/Manga of your mini wrap'
    )
    async def miniwrap_edittop(self, interaction: Interaction) -> None:
        anime_url = ''
        manga_url = ''

        async def link_modal_submit_callback(
            interaction: Interaction, anime, manga
        ) -> None:
            """Runs when the link input modal is submitted"""

            nonlocal anime_url, manga_url

            anime_url = anime
            manga_url = manga

        async def token_submit_callback(
            interaction: Interaction,
            design,
            token,
        ) -> None:
            """Runs when the token modal is submitted"""

            nonlocal anime_url, manga_url

            logger.info('TOKEN', token)
            logger.info('ANIME', anime_url)
            logger.info('MANGA', manga_url)

            pdb.set_trace()

            await interaction.response.send_message('Updates will be applied!')

        view = EditTopMiniwrapView(link_modal_submit_callback, token_submit_callback)

        await interaction.response.send_message('Edit TOP Anime/Manga', view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(AniWrapCog(bot))
