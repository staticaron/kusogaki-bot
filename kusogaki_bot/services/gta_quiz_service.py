import asyncio
import logging
import random
import uuid
from typing import Dict, List, Optional

from kusogaki_bot.models.game_config import GameConfig
from kusogaki_bot.models.game_state import GameState, Player
from kusogaki_bot.models.round_data import RoundData
from kusogaki_bot.services.anilist_service import AniListService

logger = logging.getLogger(__name__)


class GTAQuizService:
    def __init__(self):
        self.games: Dict[str, GameState] = {}
        self.anilist = AniListService()
        self.config = GameConfig()

    def _shuffle_choices(self, choices: List[str]) -> List[str]:
        """Shuffle the list of choices."""
        try:
            shuffled = choices.copy()
            random.shuffle(shuffled)
            return shuffled
        except Exception as e:
            logger.error(f'Error shuffling choices: {e}', exc_info=True)
            return choices

    def game_exists(self, channel_id: int) -> bool:
        """Check if a game exists in the given channel."""
        try:
            return any(game.channel_id == channel_id for game in self.games.values())
        except Exception as e:
            logger.error(f'Error checking game existence: {e}', exc_info=True)
            return False

    def get_game_id_by_channel(self, channel_id: int) -> Optional[str]:
        """Get game ID for a given channel."""
        try:
            return next(
                (
                    game_id
                    for game_id, game in self.games.items()
                    if game.channel_id == channel_id
                ),
                None,
            )
        except Exception as e:
            logger.error(f'Error getting game ID: {e}', exc_info=True)
            return None

    async def create_game(self, channel_id: int, creator_id: int) -> Optional[str]:
        """Create a new game instance."""
        try:
            game_id = str(uuid.uuid4())
            self.games[game_id] = GameState(
                channel_id=channel_id,
                players={creator_id: Player(hp=self.config.STARTING_HP)},
                is_active=False,
            )
            logger.info(f'Created new game {game_id} in channel {channel_id}')
            return game_id
        except Exception as e:
            logger.error(f'Error creating game: {e}', exc_info=True)
            return None

    def activate_game(self, game_id: str) -> None:
        """Activate a game."""
        try:
            if game_id in self.games:
                self.games[game_id].is_active = True
                logger.info(f'Activated game {game_id}')
        except Exception as e:
            logger.error(f'Error activating game: {e}', exc_info=True)

    def is_game_active(self, game_id: str) -> bool:
        """Check if a game is active."""
        try:
            return game_id in self.games and self.games[game_id].is_active
        except Exception as e:
            logger.error(f'Error checking game active status: {e}', exc_info=True)
            return False

    def add_player(self, channel_id: int, user_id: int) -> bool:
        """Add a player to the game."""
        try:
            game = self._get_game_by_channel(channel_id)
            if not game or game.is_active or user_id in game.players:
                return False

            game.players[user_id] = Player(hp=self.config.STARTING_HP)
            logger.info(f'Added player {user_id} to game in channel {channel_id}')
            return True
        except Exception as e:
            logger.error(f'Error adding player: {e}', exc_info=True)
            return False

    async def prepare_round(self, game_id: str) -> Optional[RoundData]:
        """Prepare a new round of the game."""
        try:
            game = self.games.get(game_id)
            if not game or not game.is_active:
                return None

            anime = await self.anilist.get_random_anime()
            correct_title = anime['title'].get('english') or anime['title'].get(
                'romaji'
            )
            wrong_answers = await self._get_wrong_answers(anime['id'])

            return RoundData(
                correct_title=correct_title,
                image_url=anime['coverImage']['large'],
                choices=self._shuffle_choices(wrong_answers + [correct_title]),
                players=game.players,
            )
        except Exception as e:
            logger.error(f'Error preparing round: {e}', exc_info=True)
            return None

    async def _get_wrong_answers(self, exclude_id: int) -> List[str]:
        """Get wrong answers for a round."""
        try:
            wrong_answers = []
            tasks = [
                self.anilist.get_random_anime() for _ in range(self.config.CHOICES - 1)
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, dict):
                    title = result['title'].get('english') or result['title'].get(
                        'romaji'
                    )
                    if result['id'] != exclude_id and title not in wrong_answers:
                        wrong_answers.append(title)

            return wrong_answers[: self.config.CHOICES - 1]
        except Exception as e:
            logger.error(f'Error getting wrong answers: {e}', exc_info=True)
            return []

    def _get_game_by_channel(self, channel_id: int) -> Optional[GameState]:
        """Get game state for a channel."""
        try:
            return next(
                (game for game in self.games.values() if game.channel_id == channel_id),
                None,
            )
        except Exception as e:
            logger.error(f'Error getting game by channel: {e}', exc_info=True)
            return None

    async def check_game_continuation(self, game_id: str) -> bool:
        """Check if the game should continue."""
        try:
            game = self.games.get(game_id)
            if not game or not game.players:
                if game:
                    await self.stop_game(game_id)
                return False
            return True
        except Exception as e:
            logger.error(f'Error checking game continuation: {e}', exc_info=True)
            return False

    async def stop_game(self, game_id: str) -> bool:
        """Stop and cleanup a game."""
        try:
            if game_id in self.games:
                self.games[game_id].is_active = False
                del self.games[game_id]
                logger.info(f'Stopped game {game_id}')
                return True
            return False
        except Exception as e:
            logger.error(f'Error stopping game: {e}', exc_info=True)
            return False

    async def process_wrong_answer(self, game_id: str, user_id: int) -> bool:
        """
        Process a wrong answer from a user.
        Returns True if the player was eliminated, False otherwise.
        """
        try:
            game = self.games.get(game_id)
            if not game or user_id not in game.players:
                return False

            game.players[user_id].hp -= 1

            if game.players[user_id].hp <= 0:
                del game.players[user_id]
                return True

            return False
        except Exception as e:
            logger.error(f'Error processing wrong answer: {e}', exc_info=True)
            return False
