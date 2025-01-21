import logging
from pathlib import Path
from typing import Set

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from kusogaki_bot.core import KusogakiBot

logger = logging.getLogger(__name__)


class ModuleReloader(FileSystemEventHandler):
    """
    A file system event handler that manages hot reloading of bot modules.

    This class extends FileSystemEventHandler to watch for file changes in the bot's
    feature directories and manages a queue of modules that need to be reloaded.

    Attributes:
        bot (KusogakiBot): The bot instance to manage reloading for
        watch_paths (Set[Path]): Set of paths to watch for changes
        base_path (Path): The base project path for relative path calculations
        reload_queue (Set[str]): Queue of feature names that need to be reloaded
    """

    def __init__(self, bot: KusogakiBot, watch_paths: Set[Path], base_path: Path):
        """Initialize the ModuleReloader."""
        self.bot = bot
        self.watch_paths = watch_paths
        self.base_path = base_path
        self.reload_queue: Set[str] = set()

    def on_modified(self, event: FileSystemEvent):
        """Handle file modification events by queueing affected modules for reload."""
        logger.info(f'File change detected: {event.src_path}')

        if not event.src_path.endswith('.py'):
            logger.debug('Ignoring non-Python file')
            return

        try:
            modified_path = Path(event.src_path).resolve()
            logger.info(f'Resolved modified path: {modified_path}')

            if self.base_path in modified_path.parents:
                rel_path = modified_path.relative_to(self.base_path)
                parts = rel_path.parts

                if (
                    len(parts) >= 2
                    and parts[0] == 'kusogaki_bot'
                    and parts[1] == 'features'
                ):
                    feature_name = parts[2]
                    self.reload_queue.add(feature_name)
                    logger.info(f'Queued reload for feature: {feature_name}')

        except Exception as e:
            logger.error(f'Error processing file change: {str(e)}', exc_info=True)

    async def process_reload_queue(self):
        """Process any pending module reloads in the queue."""
        if not self.reload_queue:
            return

        logger.info(f'Processing reload queue: {self.reload_queue}')
        for feature in list(self.reload_queue):
            try:
                cog_path = f'kusogaki_bot.features.{feature}.cog'
                logger.info(f'Attempting to reload: {cog_path}')

                if cog_path in self.bot.extensions:
                    await self.bot.reload_extension(cog_path)
                    logger.info(f'Successfully reloaded: {cog_path}')
                else:
                    logger.warning(
                        f'Extension not loaded, attempting to load: {cog_path}'
                    )
                    await self.bot.load_extension(cog_path)
                    logger.info(f'Successfully loaded: {cog_path}')

            except Exception as e:
                logger.error(f'Failed to reload {feature}: {str(e)}', exc_info=True)
            finally:
                self.reload_queue.remove(feature)


class DevelopmentService:
    """
    Service class that manages development features like hot-reloading.

    This service handles the file system watching and module reloading functionality,
    providing a clean interface for the cog to interact with these features.

    Attributes:
        bot (KusogakiBot): The bot instance this service is attached to
        observer (Observer): The file system observer for hot reloading
        reloader (ModuleReloader): The module reloader instance handling file changes
    """

    def __init__(self, bot: KusogakiBot):
        """Initialize the development service."""
        self.bot = bot
        self.observer = None
        self.reloader = None

    async def start_file_watcher(self) -> bool:
        """
        Start the file system observer for hot reloading.

        Returns:
            bool: True if the watcher was started successfully, False otherwise
        """
        if self.observer:
            return False

        base_path = self.bot.FEATURES_DIRECTORY.parent.parent.resolve()
        features_dir = self.bot.FEATURES_DIRECTORY.resolve()
        logger.info(f'Project root (absolute): {base_path}')

        watch_paths = set()
        for feature_dir in features_dir.iterdir():
            if not feature_dir.is_dir():
                continue

            cog_file = feature_dir / 'cog.py'
            if cog_file.exists():
                watch_paths.add(feature_dir.resolve())

        if not watch_paths:
            logger.warning('No valid feature directories found to watch!')
            return False

        self.reloader = ModuleReloader(self.bot, watch_paths, base_path)
        self.observer = Observer()

        watch_path = str(base_path)
        self.observer.schedule(self.reloader, watch_path, recursive=True)

        self.observer.start()
        logger.info(f'Started development file watcher with {len(watch_paths)} paths')
        return True

    def stop_file_watcher(self) -> bool:
        """
        Stop the file system observer.

        Returns:
            bool: True if the watcher was stopped successfully, False if it wasn't running
        """
        if not self.observer:
            return False

        self.observer.stop()
        self.observer.join()
        self.observer = None
        logger.info('Stopped development file watcher')
        return True

    async def process_reload_queue(self):
        """Process any pending module reloads."""
        if self.reloader:
            await self.reloader.process_reload_queue()

    def is_watching(self) -> bool:
        """
        Check if the file watcher is currently active.

        Returns:
            bool: True if the watcher is running, False otherwise
        """
        return self.observer is not None and self.observer.is_alive()
