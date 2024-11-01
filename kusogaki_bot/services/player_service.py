import logging
from datetime import datetime
from typing import Dict

from kusogaki_bot.models.events import GameEvent
from kusogaki_bot.models.game_state import Player
from kusogaki_bot.services.event_manager import GameEventManager

logger = logging.getLogger(__name__)


class PlayerService:
    def __init__(self, event_manager: GameEventManager):
        self.event_manager = event_manager

    async def add_player(
        self, game_state: Dict[str, any], user_id: int, starting_hp: int
    ) -> bool:
        if user_id in game_state['players']:
            return False

        game_state['players'][user_id] = Player(hp=starting_hp, last_answer_time=None)

        await self.event_manager.emit(
            GameEvent(
                'player_joined', {'game_id': game_state['id'], 'player_id': user_id}
            )
        )
        return True

    async def handle_player_answer(self, game_id: str, player_id: int, answer) -> bool:
        try:
            await self.event_manager.emit(
                GameEvent(
                    'answer_received',
                    {
                        'game_id': game_id,
                        'player_id': player_id,
                        'answer': answer,
                        'timestamp': datetime.now(),
                    },
                )
            )
            return True
        except Exception as e:
            logger.error(f'Error handling player answer: {e}')
            return False
