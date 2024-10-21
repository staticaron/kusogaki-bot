from discord.ext import commands
from discord import TextChannel, Embed

from utils.general import EmbedType, get_embed
from config import LOG_CHANNEL_ID

class SuggestionCog(commands.Cog):

    @commands.hybrid_command(name="suggest", description="Suggest something to the Moderators.")
    async def suggest(self, ctx: commands.Context, suggestion: str):
        channel: TextChannel = self.bot.get_channel(int(LOG_CHANNEL_ID))
        
        embd: Embed = get_embed(EmbedType.NORMAL, "Suggestion Received", suggestion, False)
        embd.add_field(
            name = "User",
            value = ctx.author.mention
        )
        
        await channel.send(embed=embd)

def setup(bot: commands.Bot):
    bot.add_cog(SuggestionCog())
