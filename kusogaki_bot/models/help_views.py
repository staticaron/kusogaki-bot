from discord import ButtonStyle, Interaction
from discord.ui import Button, View


class CommandsButton(Button):
    def __init__(self):
        super().__init__(
            style=ButtonStyle.success,
            label='View all Commands',
            custom_id='view_commands',
        )


class HelpView(View):
    def __init__(self, help_service):
        super().__init__(timeout=60)
        self.help_service = help_service
        self.add_item(CommandsButton())

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.data['custom_id'] == 'view_commands':
            embed = await self.help_service.get_all_commands_embed()
            await interaction.response.edit_message(embed=embed, view=None)
        return True
