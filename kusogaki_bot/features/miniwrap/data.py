import discord
from discord import Interaction
from discord.ui import Modal, View

from kusogaki_bot.shared.views.token_input_modal import TokenInputModal


class WrapRequest:
    def __init__(
        self,
        token,
        user,
        wt,
        anime_url: str | None = None,
        manga_url: str | None = None,
    ) -> None:
        self.token = token
        self.user = user
        self.wt = wt
        self.anime_url = anime_url
        self.manga_url = manga_url


class LinkInputModal(Modal):
    """
    Modal for accepting top anime and top manga URL
    """

    def __init__(self, submit_callback) -> None:
        super().__init__(title='Link Input')
        self.submit_callback = submit_callback

    top_anime_url = discord.ui.TextInput(
        label='Top Anime URL',
        style=discord.TextStyle.short,
        placeholder='<link to top anime>',
        required=False,
    )

    top_manga_url = discord.ui.TextInput(
        label='Top Manga URL',
        style=discord.TextStyle.short,
        placeholder='<link to top manga>',
        required=False,
    )

    async def on_submit(self, interaction: Interaction) -> None:
        await interaction.response.defer()

        await self.submit_callback(
            interaction, self.top_anime_url.value, self.top_manga_url.value
        )


class GenerateMiniwrapView(View):
    def __init__(self, submit_callback) -> None:
        super().__init__()
        self.submit_callback = submit_callback

        self.select = discord.ui.Select(
            placeholder='Style',
            options=[
                discord.SelectOption(
                    label='New',
                    value='NEW',
                    description='Colors are picked from profile banner/pfp',
                    default=True,
                ),
                discord.SelectOption(
                    label='Old',
                    value='OLD',
                    description='Colors are picked from profile color',
                ),
            ],
            required=True,
        )
        # dont do anything on selection
        self.select.callback = lambda interaction: interaction.response.defer(
            ephemeral=True
        )
        self.add_item(self.select)

        self.token_btn = discord.ui.Button(
            style=discord.ButtonStyle.gray, label='Enter Token'
        )
        self.token_btn.callback = self.token_btn_callback
        self.add_item(self.token_btn)

    async def token_btn_callback(self, interaction: Interaction) -> None:
        token_input_modal = TokenInputModal(self.submit_callback)

        await interaction.response.send_modal(token_input_modal)

        self.select.disabled = True
        self.token_btn.disabled = True

        await interaction.edit_original_response(view=self)


class EditTopMiniwrapView(View):
    def __init__(self, link_submit_callback, done_callback):
        super().__init__()
        self.link_submit_callback = link_submit_callback
        self.done_callback = done_callback

        link_input_btn = discord.ui.Button(label='EDIT', style=discord.ButtonStyle.gray)
        link_input_btn.callback = self.link_input_btn_submit

        done_btn = discord.ui.Button(label='DONE', style=discord.ButtonStyle.green)
        done_btn.callback = self.done_btn_submit

        self.add_item(link_input_btn)
        self.add_item(done_btn)

    async def link_input_btn_submit(self, interaction: Interaction) -> None:
        modal = LinkInputModal(self.link_submit_callback)
        await interaction.response.send_modal(modal)

    async def done_btn_submit(self, interaction: Interaction) -> None:
        await interaction.response.defer()
        await self.done_callback(interaction)
