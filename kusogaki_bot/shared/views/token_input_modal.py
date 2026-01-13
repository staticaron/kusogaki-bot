import discord.ui
from discord import ButtonStyle, Interaction, TextStyle
from discord.ui import Button, Modal, TextInput, View


class TokenInputModal(Modal):
    """
    Modal for accepting user token
    NOTE: Interaction is deferred
    """

    def __init__(self, submit_callback) -> None:
        super().__init__(title='Mini Wrap Input')
        self.submit_callback = submit_callback

    token = TextInput(
        label='Anilist Token',
        style=TextStyle.paragraph,
        placeholder='<paste token here>',
        required=True,
    )

    async def on_submit(self, interaction: Interaction) -> None:
        await interaction.response.defer()
        await self.submit_callback(interaction, self.token.value)


class TokenInputView(View):
    """
    View with a button to spawn TokenInputModal
    """

    def __init__(self, token_submit_callback):
        super().__init__()
        self.token_submit_callback = token_submit_callback

        self.token_btn = Button(style=ButtonStyle.grey, label='Enter Token')
        self.token_btn.callback = self.token_btn_on_submit

        self.add_item(self.token_btn)

    async def token_btn_on_submit(self, interaction: Interaction) -> None:
        token_input_modal = TokenInputModal(submit_callback=self.token_submit_callback)
        await interaction.response.send_modal(token_input_modal)
        self.token_btn.disabled = True
        await interaction.edit_original_response(view=self)
