import logging

from discord.ext import commands

from kusogaki_bot.core import BaseCog, KusogakiBot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReloadCog(BaseCog):
    """
    Cog for basic ping command to check bot latency
    """

    def __init__(self, bot: KusogakiBot):
        super().__init__(bot)

    @commands.command(name='reload', description="Check the bot's latency")
    async def reload_cmd(self, ctx: commands.Context, module: str):
        """
        Reload a module

        Args:
            ctx (commands.Context): The command context
        """

        modules = []
        for feature_dir in ctx.bot.FEATURES_DIRECTORY.iterdir():
            if not feature_dir.is_dir():
                continue

            cog_file = feature_dir / 'cog.py'
            if not cog_file.exists():
                continue

            modules.append(feature_dir.name)

        if module not in modules:
            return await ctx.send('No matching cog found.')

        cog_path = f'kusogaki_bot.features.{module}.cog'
        await ctx.bot.reload_extension(cog_path)

        await ctx.send(f'Reloaded module: `{module}`')


async def setup(bot: KusogakiBot):
    await bot.add_cog(ReloadCog(bot))
