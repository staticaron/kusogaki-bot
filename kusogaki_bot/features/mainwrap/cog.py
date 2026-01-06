from discord import Interaction
from discord.ext import commands

from kusogaki_bot.features.mainwrap.data import EditTopView, MediaLinkType
from kusogaki_bot.features.mainwrap.task_manager import EditTopTask, EditTopTaskManager
from kusogaki_bot.features.miniwrap.data import TokenInputModal


class MainWrapCog(commands.Cog):
    def __init__(self, bot) -> None:
        super().__init__()
        self.bot = bot
        self.task_manager = EditTopTaskManager(bot)

    @commands.hybrid_command(
        name='edittop', description='Edit Top Anime/Manga of your wrap'
    )
    async def editop(self, ctx: commands.Context) -> None:
        anime_urls = ()
        manga_urls = ()

        async def anime_link_modal_submit(
            link_type: MediaLinkType, urls: tuple[str]
        ) -> None:
            """Runs when the link modal is submitted"""

            global anime_urls, manga_urls

            if link_type is MediaLinkType.ANIME:
                anime_urls = urls
            else:
                manga_urls = urls

        async def view_submit(interaction: Interaction) -> None:
            """Runs when the submit button on view is pressed"""

            global anime_urls, manga_urls, user_token

            async def token_submit_callback(
                interaction: Interaction, token: str
            ) -> None:
                await self.task_manager.edit_top_tasks.put(
                    EditTopTask(token, anime_urls, manga_urls)
                )

                if not self.task_manager.process_edit_top.is_running():
                    self.task_manager.process_edit_top.start()

                await interaction.followup.send(
                    'Processing! Check back after some time!'
                )

            token_modal = TokenInputModal(token_submit_callback, 'NEW')

            await interaction.response.send_modal(token_modal)

        view = EditTopView(anime_link_modal_submit, view_submit)

        await ctx.send('Edit Top Media', view=view)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MainWrapCog(bot))
