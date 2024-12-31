from typing import Optional

from discord.ext import commands

from kusogaki_bot.models.help_views import HelpView
from kusogaki_bot.services.help_service import HelpService


class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.help_service = HelpService()

    @commands.command(name='help', description='Get help with bot commands')
    async def help(self, ctx: commands.Context, command: Optional[str] = None):
        if command:
            embed = await self.help_service.get_command_help(command)
            if embed:
                await ctx.send(embed=embed)
            else:
                error_embed = await self.help_service.get_command_not_found_embed(
                    command
                )
                await ctx.send(embed=error_embed)
        else:
            embed = await self.help_service.get_overview_embed()
            view = HelpView(self.help_service)
            await ctx.send(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))
