from discord.ext import commands
from discord import TextChannel, Embed

from utils.general import EmbedType, get_embed
from config import LOG_CHANNEL_ID

class SuggestionCog(commands.Cog):

    bot: commands.Bot = None

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="suggest", description="Suggest something to the Moderators.")
    async def suggest(self, ctx: commands.Context, *suggestion):
        channel: TextChannel = self.bot.get_channel(int(LOG_CHANNEL_ID))
        
        embd: Embed = await get_embed(EmbedType.NORMAL, "Suggestion Received", " ".join(suggestion), False)
        embd.add_field(
            name = "User",
            value = ctx.author.mention
        )
        
        await channel.send(embed=embd)

async def setup(bot: commands.Bot):
    await bot.add_cog(SuggestionCog(bot))
