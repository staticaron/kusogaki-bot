import pdb

from discord import Interaction, Permissions, app_commands
from discord.ext import commands

from kusogaki_bot.core import BaseCog, KusogakiBot
from kusogaki_bot.features.miniwrap.data import (
    EditTopMiniwrapView,
    GenerateMiniwrapView,
    WrapRequest,
)
from kusogaki_bot.features.miniwrap.generation_service import AniWrapService
from kusogaki_bot.features.miniwrap.generation_task_manager import TaskManager
from kusogaki_bot.shared.utils.embeds import EmbedType, get_embed
from kusogaki_bot.shared.views.token_input_modal import TokenInputView
from kusogaki_bot.features.miniwrap.fetch_data import fetch_img_url_from_media_url


@app_commands.guild_only()
class MiniWrapGroup(app_commands.Group):
    pass


class AniWrapCog(BaseCog):
    miniwrapgroup = MiniWrapGroup(
        name='miniwrap',
        description='Holder for commands related to miniwrap',
    )

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

            await self.task_manager.add_to_queue(
                WrapRequest(token, interaction.user, style)
            )

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
        """
        Edit the top anime/manga for miniwrap
        """

        anime_img_url = ''
        manga_img_url = ''

        async def link_modal_submit_callback(
            interaction: Interaction, anime, manga
        ) -> None:
            """Runs when the link input modal is submitted"""

            nonlocal anime_img_url, manga_img_url

            anime_img_url = (
                await fetch_img_url_from_media_url(anime) if anime != '' else ''
            )
            manga_img_url = (
                await fetch_img_url_from_media_url(manga) if manga != '' else ''
            )

            if anime_img_url is None or manga_img_url is None:
                await interaction.followup.send('Media URL Error!', ephemeral=True)

        async def link_modal_done_callback(
            interaction: Interaction,
        ) -> None:
            """Runs when the token modal is submitted"""

            nonlocal anime_img_url, manga_img_url

            async def submit_callback(interaction: Interaction, token: str) -> None:
                await interaction.followup.send('You will receive updated wrap soon!')

                await self.task_manager.add_to_queue(
                    WrapRequest(
                        token, interaction.user, 'NEW', anime_img_url, manga_img_url
                    )
                )

            view = TokenInputView(submit_callback)
            embd, _ = await get_embed(
                EmbedType.NORMAL,
                'Pick Design',
                '[click here](https://anilist.co/api/v2/oauth/authorize?client_id=8704&response_type=token) to get your anilist token!',
            )

            await interaction.followup.send(
                embed=embd,
                view=view,
                ephemeral=True,
            )

        view = EditTopMiniwrapView(link_modal_submit_callback, link_modal_done_callback)

        await interaction.response.send_message('Edit Top Media', view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(AniWrapCog(bot))
