import logging
from pathlib import Path
from typing import List

from discord import Intents, Message
from discord.ext import commands

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KusogakiBot(commands.AutoShardedBot):
    """
    Discord bot class with improved structure and error handling
    """

    DEFAULT_PREFIX = ['kuso ', 'KUSO ', 'Kuso ']
    COGS_DIRECTORY = Path('kusogaki_bot/cogs')

    def __init__(self) -> None:
        intents = Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(
            command_prefix=self.get_prefix,
            intents=intents,
            help_command=None,
        )

    async def get_prefix(self, message: Message) -> List[str]:
        """
        Get the command prefix for the bot
        Returns both mention and custom prefixes
        """
        return commands.when_mentioned_or(*self.DEFAULT_PREFIX)(self, message)

    async def load_cogs(self) -> None:
        """
        Load all cog extensions from the cogs directory
        Handles errors for individual cog loading
        """
        if not self.COGS_DIRECTORY.exists():
            logger.error(f'Cogs directory not found: {self.COGS_DIRECTORY}')
            return

        for cog_file in self.COGS_DIRECTORY.glob('*.py'):
            if cog_file.stem.startswith('__'):
                continue

            try:
                cog_path = f'kusogaki_bot.cogs.{cog_file.stem}'
                await self.load_extension(cog_path)
                logger.info(f'Loaded extension: {cog_path}')
            except Exception as e:
                logger.error(f'Failed to load extension {cog_path}: {str(e)}')

    async def setup_hook(self) -> None:
        """
        Setup hook called before the bot starts
        """
        await self.load_cogs()

    async def on_ready(self) -> None:
        """
        Called when the bot has successfully connected to Discord
        """
        logger.info(f'Logged in as {self.user.name}')
        logger.info(f'Bot is in {len(self.guilds)} guilds')

    async def on_error(self, event: str, *args, **kwargs) -> None:
        """
        Global error handler for the bot

        Args:
            event: The name of the event that raised the error
            args: Positional arguments that were passed to the event
            kwargs: Keyword arguments that were passed to the event
        """
        logger.error(f'Error in event {event}')
        if args:
            logger.error(f'Event args: {args}')
        if kwargs:
            logger.error(f'Event kwargs: {kwargs}')
        logger.error('Full traceback:', exc_info=True)
