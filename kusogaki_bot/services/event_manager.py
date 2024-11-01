import logging
from typing import Callable, Dict, List

from kusogaki_bot.models.events import GameEvent

logger = logging.getLogger(__name__)


class GameEventManager:
    def __init__(self):
        self.handlers: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, handler: Callable):
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
        logger.debug(f'Handler subscribed to {event_type}')

    async def emit(self, event: GameEvent):
        if event.type in self.handlers:
            logger.debug(f'Emitting event {event.type}')
            for handler in self.handlers[event.type]:
                try:
                    await handler(event.data)
                except Exception as e:
                    logger.error(f'Error in event handler for {event.type}: {e}')
