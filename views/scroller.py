from discord import Embed, ButtonStyle
from discord.ui import View, Button
from discord import ui, Interaction

from config import PREV_EMOTE, NEXT_EMOTE, FIRST_EMOTE, LAST_EMOTE


class Scroller(View):

    pages: list[Embed] = None
    current_page: int = 0

    def __init__(self, pages):
        super().__init__(timeout=100)
        self.pages = pages
        
    async def update(self, interaction: Interaction):
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)
        
    @ui.button(style=ButtonStyle.gray, disabled=True, emoji=FIRST_EMOTE)
    async def first_page(self, interaction: Interaction, button: Button):
        
        self.current_page = 0
        self.children[0].disabled = True
        self.children[1].disabled = True
        self.children[2].disabled = False
        self.children[3].disabled = False
                
        await self.update(interaction)
        
    @ui.button(style=ButtonStyle.gray, disabled=True, emoji=PREV_EMOTE)
    async def previous_page(self, interaction: Interaction, button: Button):
        if self.current_page > 0:
            self.current_page = self.current_page - 1
            self.children[2].disabled = False
            self.children[3].disabled = False
            
            if self.current_page == 0:
                self.children[0].disabled = True
                self.children[1].disabled = True
            
            await self.update(interaction)
            
    @ui.button(style=ButtonStyle.gray, disabled=False, emoji=NEXT_EMOTE)
    async def next_page(self, interaction: Interaction, button: Button):
        if self.current_page < len(self.pages) - 1:
            self.current_page = self.current_page + 1
            self.children[0].disabled = False
            self.children[1].disabled = False
            
            if self.current_page == len(self.pages) - 1:
                self.children[2].disabled = True
                self.children[3].disabled = True
            
            await self.update(interaction)
        
    @ui.button(style=ButtonStyle.gray, disabled=False, emoji=LAST_EMOTE)
    async def last_page(self, interaction: Interaction, button: Button):
        
        self.current_page = len(self.pages) - 1
        self.children[0].disabled = False
        self.children[1].disabled = False
        self.children[2].disabled = True
        self.children[3].disabled = True
                
        await self.update(interaction)    
