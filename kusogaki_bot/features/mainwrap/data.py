import pdb
from enum import Enum
from os import link

from discord import ButtonStyle, Interaction, TextStyle
from discord.ui import Button, Modal, TextInput, View, button


class MediaLinkType(Enum):
    ANIME = 0
    MANGA = 1


class MediaLinkInputModal(Modal):
    """Modal used for accepting 5 links"""

    link1 = TextInput(
        label='1st',
        style=TextStyle.short,
        placeholder='URL or ID',
        required=False,
    )
    link2 = TextInput(
        label='2nd',
        style=TextStyle.short,
        placeholder='URL or ID',
        required=False,
    )
    link3 = TextInput(
        label='3rd',
        style=TextStyle.short,
        placeholder='URL or ID',
        required=False,
    )
    link4 = TextInput(
        label='4th',
        style=TextStyle.short,
        placeholder='URL or ID',
        required=False,
    )
    link5 = TextInput(
        label='5th',
        style=TextStyle.short,
        placeholder='URL or ID',
        required=False,
    )

    def __init__(
        self,
        submit_callback,
        title: str,
        link_type: MediaLinkType = MediaLinkType.ANIME,
    ) -> None:
        super().__init__(title=title)
        self.title = title
        self.submit_callback = submit_callback
        self.link_type = link_type

    async def on_submit(self, interaction: Interaction) -> None:
        await interaction.response.defer()

        await self.submit_callback(
            self.link_type,
            (
                self.link1.value,
                self.link2.value,
                self.link3.value,
                self.link4.value,
                self.link5.value,
            ),
        )


class EditTopView(View):
    def __init__(self, modal_submit_callback, view_submit_callback):
        super().__init__()
        self.modal_submit_callback = modal_submit_callback
        self.view_submit_callback = view_submit_callback

    @button(label='ANIME', style=ButtonStyle.gray)
    async def anime_btn(self, interaction: Interaction, btn: Button) -> None:
        anime_link_input = MediaLinkInputModal(
            self.modal_submit_callback, 'Anime Link', MediaLinkType.ANIME
        )

        await interaction.response.send_modal(anime_link_input)

    @button(label='MANGA', style=ButtonStyle.gray)
    async def manga_btn(self, interaction: Interaction, btn: Button) -> None:
        manga_link_input = MediaLinkInputModal(
            self.modal_submit_callback, 'Manga Link', MediaLinkType.MANGA
        )

        await interaction.response.send_modal(manga_link_input)

    @button(label='DONE', style=ButtonStyle.green)
    async def submit_btn(self, interaction: Interaction, btn: Button) -> None:
        pdb.set_trace()
        await self.view_submit_callback()
