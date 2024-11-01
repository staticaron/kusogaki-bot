import discord

from kusogaki_bot.data.food_counter_repository import FoodCounterRepository
from kusogaki_bot.utils.embeds import EmbedType, get_embed


class FoodCounterService:
    def __init__(self):
        self.db = FoodCounterRepository()

    def increment_counter(self, user_id: str) -> int:
        """Increment food counter for a user and return new count"""
        counter = self.db.get_counter(user_id)
        new_count = counter.increment()
        self.db.save_counter(counter)
        return new_count

    def get_count(self, user_id: str) -> int:
        """Get current count for a user"""
        counter = self.db.get_counter(user_id)
        return counter.count

    async def create_mention_embed(
        self, user_mention: str, count: int
    ) -> tuple[discord.Embed, discord.File]:
        """Create embed for food mention command"""
        description = f"{user_mention}, your caseoh is showing! Adding to the total amount of times you've mentioned food. Total is now: {count}"

        embed = await get_embed(
            type=EmbedType.NORMAL,
            title='Awaiz has mentioned food!',
            description=description,
        )

        file = discord.File('static/awaiz.png', filename='awaiz.png')
        embed.set_image(url='attachment://awaiz.png')

        return embed, file

    async def create_count_embed(
        self, user_mention: str, count: int
    ) -> tuple[discord.Embed, discord.File]:
        """Create embed for food count command"""
        description = f"He's eaten everything. {user_mention} has talked about food {count} time(s). I guess he'll start eating drywall soon"

        embed = await get_embed(
            type=EmbedType.NORMAL, title='Awaiz Food Counter', description=description
        )

        file = discord.File('static/eatdrywall.gif', filename='eatdrywall.gif')
        embed.set_image(url='attachment://eatdrywall.gif')

        return embed, file
