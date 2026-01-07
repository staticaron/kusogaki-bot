import discord
from discord import Interaction
from discord.ext import commands

from kusogaki_bot.features.mainwrap.data import EditTopView, MediaLinkType
from kusogaki_bot.features.mainwrap.task_manager import EditTopTask, EditTopTaskManager
from kusogaki_bot.features.miniwrap.data import TokenInputModal
from kusogaki_bot.shared.utils.embeds import EmbedType, get_embed


class MainWrapCog(commands.Cog):
    def __init__(self, bot) -> None:
        super().__init__()
        self.bot = bot
        self.task_manager = EditTopTaskManager(bot)
        self.anime_urls = ()
        self.manga_urls = ()

    @commands.hybrid_command(
        name='edittop', description='Edit Top Anime/Manga of your wrap'
    )
    async def editop(self, ctx: commands.Context) -> None:
        async def anime_link_modal_submit(
            link_type: MediaLinkType, urls: tuple[str]
        ) -> None:
            """Runs when the link modal is submitted"""
            if link_type is MediaLinkType.ANIME:
                self.anime_urls = urls
            else:
                self.manga_urls = urls

        async def view_submit(interaction: Interaction) -> None:
            """Runs when the submit button on view is pressed"""

            async def token_submit_callback(
                interaction: Interaction, design: str, token: str
            ) -> None:
                if not token or not token.strip():
                    return
                await self.task_manager.edit_top_tasks.put(
                    EditTopTask(token, self.anime_urls, self.manga_urls, interaction.user)
                )
                if not self.task_manager.process_edit_top.is_running():
                    self.task_manager.process_edit_top.start()

            async def token_btn_callback(interaction: Interaction) -> None:
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

            await interaction.response.send_message(embed=embd, view=token_view, ephemeral=True)

        view = EditTopView(anime_link_modal_submit, view_submit)

        await ctx.send('Edit Top Media', view=view)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MainWrapCog(bot))
