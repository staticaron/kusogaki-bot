import discord
from discord import Interaction, app_commands, user
from discord.ext import commands

from kusogaki_bot.features.mainwrap.data import EditTopView, MediaLinkType
from kusogaki_bot.features.mainwrap.task_manager import EditTopTask, EditTopTaskManager
from kusogaki_bot.features.miniwrap.data import TokenInputModal
from kusogaki_bot.shared.utils.embeds import EmbedType, get_embed


class MainWrapGroup(app_commands.Group):
    pass


class MainWrapCog(commands.Cog):
    mainwrapgroup = MainWrapGroup(
        name='mainwrap', description='Holder for MainWrap Commands'
    )

    def __init__(self, bot) -> None:
        super().__init__()
        self.bot = bot
        self.task_manager = EditTopTaskManager(bot)

    @mainwrapgroup.command(
        name='edittop', description='Edit the TOP Anime/Manga for the mainwrap'
    )
    async def edittop(self, interaction: Interaction) -> None:
        anime_urls = ()
        manga_urls = ()

        async def anime_link_modal_submit(
            link_type: MediaLinkType, urls: tuple[str]
        ) -> None:
            """Runs when the link modal is submitted"""

            nonlocal anime_urls, manga_urls

            if link_type is MediaLinkType.ANIME:
                anime_urls = urls
            else:
                manga_urls = urls

        async def view_submit(interaction: Interaction) -> None:
            """Runs when the submit button on view is pressed"""

            async def token_submit_callback(
                interaction: Interaction, design: str, token: str
            ) -> None:
                """
                Runs when the token input modal is submitted!
                Adds a new entry to pending edittop task entries
                """

                nonlocal anime_urls, manga_urls

                if not token or not token.strip():
                    return

                await self.task_manager.edit_top_tasks.put(
                    EditTopTask(token, anime_urls, manga_urls, interaction.user)
                )
                if not self.task_manager.process_edit_top.is_running():
                    self.task_manager.process_edit_top.start()

            async def token_btn_callback(interaction: Interaction) -> None:
                """
                Runs when the Token button is pressed
                Responsible for sending the token input modal
                """

                token_input_modal = TokenInputModal(token_submit_callback, 'NEW')
                await interaction.response.send_modal(token_input_modal)
                self.token_btn.disabled = True
                await interaction.edit_original_response(view=token_view)

            self.token_btn = discord.ui.Button(
                style=discord.ButtonStyle.gray, label='Enter Token'
            )
            self.token_btn.callback = token_btn_callback

            token_view = discord.ui.View()
            token_view.add_item(self.token_btn)

            embd, _ = await get_embed(
                EmbedType.NORMAL,
                'Enter Token',
                '[click here](https://anilist.co/api/v2/oauth/authorize?client_id=34187&response_type=token) to get your anilist token!',
            )

            await interaction.response.send_message(
                embed=embd, view=token_view, ephemeral=True
            )

        view = EditTopView(anime_link_modal_submit, view_submit)

        await interaction.response.send_message('Edit Top Media', view=view)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MainWrapCog(bot))
