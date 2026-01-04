import pdb

import discord
from discord import Interaction
from discord.ui import Modal, View


class MiniWrapInputModal(Modal):
    def __init__(self, submit_callback, design: str = 'NEW') -> None:
        super().__init__(title='Mini Wrap Input')
        self.submit_callback = submit_callback
        self.design = design

    token = discord.ui.TextInput(
        label='Anilist Token',
        style=discord.TextStyle.paragraph,
        placeholder='<paste token here>',
        required=True,
    )

    async def on_submit(self, interaction: Interaction) -> None:
        await interaction.response.send_message(
            'You will receive your wrap in DMs shortly!', ephemeral=True
        )
        await self.submit_callback(interaction, self.design, self.token.value)


class MiniWrapMainView(View):
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

        self.submit_btn = discord.ui.Button(
            style=discord.ButtonStyle.gray, label='Enter Token'
        )
        self.submit_btn.callback = self.enter_token_callback
        self.add_item(self.submit_btn)

    async def enter_token_callback(self, interaction: Interaction) -> None:
        token_input_modal = MiniWrapInputModal(
            self.submit_callback, self.select.values[0]
        )

        self.select.disabled = True
        self.submit_btn.disabled = True

        await interaction.response.send_modal(token_input_modal)
