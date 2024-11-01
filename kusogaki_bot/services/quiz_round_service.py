import asyncio
import logging
import random
from typing import Dict, List, Optional, Set

from kusogaki_bot.models.events import GameEvent
from kusogaki_bot.models.game_config import GameConfig
from kusogaki_bot.models.round_data import RoundData
from kusogaki_bot.services.anilist_service import AniListService
from kusogaki_bot.services.event_manager import GameEventManager

logger = logging.getLogger(__name__)


class QuizRoundService:
    def __init__(
        self, anilist_service: AniListService, event_manager: GameEventManager
    ):
        self.anilist = anilist_service
        self.event_manager = event_manager
        self.current_rounds: Dict[str, RoundData] = {}
        self.config = GameConfig()
        self.recently_used_titles: Set[str] = set()
        self.max_recent_titles = 50
        self.current_rounds: Dict[str, RoundData] = {}
        self.round_locks: Dict[str, asyncio.Lock] = {}

    async def prepare_round(
        self, game_id: str, players: Dict[int, any]
    ) -> Optional[RoundData]:
        """Prepare a new round of the game."""
        if game_id not in self.round_locks:
            self.round_locks[game_id] = asyncio.Lock()

        async with self.round_locks[game_id]:
            try:
                if game_id in self.current_rounds:
                    del self.current_rounds[game_id]

                anime = await self.anilist.get_random_anime()
                round_data = await self._create_round_data(anime, players)
                self.current_rounds[game_id] = round_data

                await self.event_manager.emit(
                    GameEvent(
                        type='round_prepared',
                        data={'game_id': game_id, 'round_data': round_data},
                    )
                )

                return round_data

            except Exception as e:
                logger.error(f'Error preparing round: {e}')
                return None

    async def _create_round_data(
        self, anime: Dict, players: Dict[int, any]
    ) -> RoundData:
        """Create round data from anime information."""
        try:
            correct_title = anime['title'].get('english') or anime['title'].get(
                'romaji'
            )
            wrong_choices = await self._get_choices(anime)

            while len(wrong_choices) < self.config.CHOICES - 1:
                wrong_choices.append(f'Unknown Anime {len(wrong_choices) + 1}')
                logger.warning(
                    'Had to add placeholder choice due to insufficient options'
                )

            all_choices = wrong_choices + [correct_title]
            random.shuffle(all_choices)

            return RoundData(
                correct_title=correct_title,
                image_url=anime['coverImage']['large'],
                choices=all_choices,
                players=players,
            )
        except Exception as e:
            logger.error(f'Error creating round data: {e}')
            raise

    async def _get_choices(self, correct_anime: Dict) -> List[str]:
        """Get wrong answer choices for the round."""
        try:
            correct_title = correct_anime['title'].get('english') or correct_anime[
                'title'
            ].get('romaji')
            wrong_answers = set()
            attempts = 0
            max_attempts = 10

            tasks = []
            for _ in range(self.config.CHOICES * 2):
                tasks.append(self.anilist.get_random_anime())

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if len(wrong_answers) >= self.config.CHOICES - 1:
                    break

                if isinstance(result, Exception):
                    logger.warning(f'Error fetching wrong choice: {result}')
                    continue

                try:
                    title = result['title'].get('english') or result['title'].get(
                        'romaji'
                    )

                    if (
                        title
                        and title != correct_title
                        and title not in wrong_answers
                        and title not in self.recently_used_titles
                    ):
                        wrong_answers.add(title)
                except Exception as e:
                    logger.warning(f'Error processing wrong choice: {e}')
                    continue

            while (
                len(wrong_answers) < self.config.CHOICES - 1 and attempts < max_attempts
            ):
                try:
                    anime = await self.anilist.get_random_anime()
                    title = anime['title'].get('english') or anime['title'].get(
                        'romaji'
                    )

                    if (
                        title
                        and title != correct_title
                        and title not in wrong_answers
                        and title not in self.recently_used_titles
                    ):
                        wrong_answers.add(title)
                except Exception as e:
                    logger.warning(f'Error in additional choice fetch: {e}')

                attempts += 1

            wrong_answers_list = list(wrong_answers)[: self.config.CHOICES - 1]

            if len(wrong_answers_list) < self.config.CHOICES - 1:
                logger.warning(
                    f'Could only get {len(wrong_answers_list)} wrong choices '
                    f'instead of {self.config.CHOICES - 1}'
                )

            return wrong_answers_list

        except Exception as e:
            logger.error(f'Error getting wrong choices: {e}')
            return []

    async def get_current_round(self, game_id: str) -> Optional[RoundData]:
        """Get the current round data for a game."""
        return self.current_rounds.get(game_id)

    async def clear_round(self, game_id: str):
        """Clear the round data for a game."""
        try:
            if game_id in self.current_rounds:
                del self.current_rounds[game_id]
            if game_id in self.round_locks:
                del self.round_locks[game_id]
        except Exception as e:
            logger.error(f'Error clearing round: {e}')

    def _generate_placeholder_choices(self, count: int) -> List[str]:
        """Generate placeholder choices if needed."""
        return [f'Alternative Anime {i+1}' for i in range(count)]
