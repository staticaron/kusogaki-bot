import asyncio
import logging

from discord.ext import commands

from kusogaki_bot.core import BaseCog, KusogakiBot
from kusogaki_bot.features.development.service import DevelopmentService

logger = logging.getLogger(__name__)


class DevelopmentCog(BaseCog):
    """
    Development utilities cog with hot-reloading capability.

    This cog provides development-focused features including hot-reloading of
    modules when their source files are modified. It uses the DevelopmentService
    to manage file watching and module reloading functionality.

    Attributes:
        bot (KusogakiBot): The bot instance this cog is attached to
        service (DevelopmentService): The development service handling file watching
    """

    def __init__(self, bot: KusogakiBot):
        """Initialize the development cog."""
        super().__init__(bot)
        self.service = DevelopmentService(bot)

    def cog_unload(self):
        """Clean up when the cog is unloaded."""
        self.service.stop_file_watcher()

    @commands.command(name='dev')
    @commands.is_owner()
    async def toggle_dev_mode(self, ctx: commands.Context):
        """
        Toggle development mode with hot-reloading.

        This command toggles the development mode on/off. When enabled, it starts
        the file watcher for hot reloading. When disabled, it stops the watcher.

        Args:
            ctx (commands.Context): The command context
        """
        if self.service.is_watching():
            if self.service.stop_file_watcher():
                await ctx.send('Development mode disabled')
            else:
                await ctx.send('Failed to disable development mode')
        else:
            if await self.service.start_file_watcher():
                await ctx.send('Development mode enabled')
            else:
                await ctx.send('Failed to enable development mode')

    async def process_reload_loop(self):
        """Process the reload queue periodically."""
        logger.info('Starting reload processing loop')
        try:
            while True:
                await self.service.process_reload_queue()
                await asyncio.sleep(1)
        except Exception as e:
            logger.error(f'Error in reload loop: {str(e)}', exc_info=True)

    @commands.Cog.listener()
    async def on_ready(self):
        """Start the reload processing loop when the bot is ready."""
        logger.info('Development cog ready, starting reload loop')
        self.bot.loop.create_task(self.process_reload_loop())


async def setup(bot: KusogakiBot):
    await bot.add_cog(DevelopmentCog(bot))
