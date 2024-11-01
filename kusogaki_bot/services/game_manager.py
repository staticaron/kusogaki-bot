import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, Optional, Set

import discord

from kusogaki_bot.models.events import GameEvent
from kusogaki_bot.models.game_config import GameConfig
from kusogaki_bot.models.game_state import GameState, Player
from kusogaki_bot.services.event_manager import GameEventManager
from kusogaki_bot.services.message_service import MessageService
from kusogaki_bot.services.player_service import PlayerService
from kusogaki_bot.services.quiz_round_service import QuizRoundService

logger = logging.getLogger(__name__)


class GameManager:
    def __init__(
        self,
        event_manager: GameEventManager,
        round_service: QuizRoundService,
        player_service: PlayerService,
        message_service: MessageService,
        config: GameConfig,
    ):
        self.games: Dict[str, GameState] = {}
        self.event_manager = event_manager
        self.round_service = round_service
        self.player_service = player_service
        self.message_service = message_service
        self.config = config
        self.answered_this_round: Dict[str, Set[int]] = {}
        self.active_rounds: Dict[str, asyncio.Task] = {}
        self.round_locks: Dict[str, asyncio.Lock] = {}
        self.current_round_messages: Dict[str, discord.Message] = {}

    async def create_game(self, channel_id: int, creator_id: int) -> Optional[str]:
        try:
            game_id = str(uuid.uuid4())
            self.games[game_id] = GameState(
                channel_id=channel_id,
                players={creator_id: Player(hp=self.config.STARTING_HP)},
                start_time=datetime.now(),
            )
            self.answered_this_round[game_id] = set()
            await self.event_manager.emit(
                GameEvent(type='game_created', data={'game_id': game_id})
            )
            return game_id
        except Exception as e:
            logger.error(f'Error creating game: {e}')
            return None

    async def start_game(self, game_id: str):
        if game_id not in self.games:
            return False

        self.games[game_id].is_active = True
        await self.run_game(game_id)
        return True

    def check_reaction(self, game_id: str, reaction, user) -> bool:
        game_state = self.games.get(game_id)
        if not game_state or not game_state.is_active:
            return False
        if user.bot or user.id not in game_state.players:
            return False
        if user.id in self.answered_this_round.get(game_id, set()):
            return False

        try:
            choice_num = int(str(reaction.emoji)[0])
            return 1 <= choice_num <= self.config.CHOICES
        except (ValueError, IndexError):
            return False

    async def run_game(self, game_id: str):
        """Main game loop."""
        try:
            game_state = self.games[game_id]
            self.round_locks[game_id] = asyncio.Lock()

            while game_state.is_active:
                async with self.round_locks[game_id]:
                    round_data = await self.round_service.prepare_round(
                        game_id, game_state.players
                    )
                    if not round_data:
                        break

                    self.answered_this_round[game_id] = set()
                    round_start_time = asyncio.get_event_loop().time()

                    message = await self.message_service.handle_round(
                        game_state.channel_id, game_id, round_data
                    )
                    if not message:
                        break

                    end_time = round_start_time + self.config.GUESS_TIME
                    correct_answer_given = False
                    active_players = set(round_data.players.keys())
                    round_results = []
                    any_answer_given = False

                while (
                    asyncio.get_event_loop().time() < end_time
                    and not correct_answer_given
                    and len(self.answered_this_round[game_id]) < len(active_players)
                ):
                    try:
                        timeout = max(
                            0.1,
                            min(
                                end_time - asyncio.get_event_loop().time(),
                                round_start_time
                                + self.config.ROUND_TIMEOUT
                                - asyncio.get_event_loop().time(),
                            ),
                        )

                        reaction, user = await self.message_service.wait_for_reaction(
                            message,
                            timeout=timeout,
                            check=lambda r, u: self.check_reaction(game_id, r, u),
                        )

                        any_answer_given = True
                        self.answered_this_round[game_id].add(user.id)

                        choice_idx = int(str(reaction.emoji)[0]) - 1
                        selected_answer = round_data.choices[choice_idx]

                        if selected_answer == round_data.correct_title:
                            game_state.players[user.id].correct_guesses += 1
                            round_results.append(
                                {'user': user, 'correct': True, 'eliminated': False}
                            )
                            correct_answer_given = True
                        else:
                            eliminated = await self.process_wrong_answer(
                                game_id, user.id
                            )
                            round_results.append(
                                {
                                    'user': user,
                                    'correct': False,
                                    'eliminated': eliminated,
                                }
                            )

                    except asyncio.TimeoutError:
                        if (
                            not any_answer_given
                            and asyncio.get_event_loop().time()
                            >= round_start_time + self.config.ROUND_TIMEOUT
                        ):
                            await self.message_service.send_timeout_message(
                                game_state.channel_id,
                                self.config.ROUND_TIMEOUT,
                                round_data.correct_title,
                            )
                            await self.end_game(game_id)
                            return

                unanswered_players = active_players - self.answered_this_round[game_id]
                for player_id in unanswered_players:
                    eliminated = await self.process_wrong_answer(game_id, player_id)
                    round_results.append(
                        {
                            'user_id': player_id,
                            'correct': False,
                            'eliminated': eliminated,
                            'timeout': True,
                        }
                    )

                is_game_over = all(
                    player.hp <= 0 for player in game_state.players.values()
                )
                final_scores = None
                if is_game_over or len(game_state.players) == 0:
                    final_scores = {}
                    for result in round_results:
                        if 'user' in result:
                            player_id = result['user'].id
                            if player_id in game_state.players:
                                final_scores[player_id] = {
                                    'hp': game_state.players[player_id].hp,
                                    'correct': game_state.players[
                                        player_id
                                    ].correct_guesses,
                                }
                        elif 'user_id' in result:
                            player_id = result['user_id']
                            if player_id in game_state.players:
                                final_scores[player_id] = {
                                    'hp': game_state.players[player_id].hp,
                                    'correct': game_state.players[
                                        player_id
                                    ].correct_guesses,
                                }

                await self.message_service.send_round_results(
                    game_state.channel_id,
                    round_results,
                    round_data.correct_title,
                    is_game_over=is_game_over,
                    final_scores=final_scores,
                )

                if is_game_over or not await self.check_game_continuation(game_id):
                    break

                await asyncio.sleep(3)

        except Exception as e:
            logger.error(f'Error in game loop: {e}')
        finally:
            if game_id in self.round_locks:
                del self.round_locks[game_id]
            if game_id in self.current_round_messages:
                del self.current_round_messages[game_id]
            await self.end_game(game_id)

    async def process_wrong_answer(self, game_id: str, user_id: int) -> bool:
        """Process a wrong answer. Returns True if player was eliminated."""
        game = self.games.get(game_id)
        if not game or user_id not in game.players:
            return False

        game.players[user_id].hp -= 1
        return False

    async def check_game_continuation(self, game_id: str) -> bool:
        """Check if the game should continue."""
        game = self.games.get(game_id)
        return game and game.players and game.is_active

    async def end_game(self, game_id: str) -> bool:
        """End and cleanup a game."""
        try:
            if game_id in self.games:
                channel_id = self.games[game_id].channel_id
                self.games[game_id].is_active = False

                if game_id in self.answered_this_round:
                    del self.answered_this_round[game_id]
                if game_id in self.active_rounds:
                    self.active_rounds[game_id].cancel()
                    del self.active_rounds[game_id]
                if game_id in self.round_locks:
                    del self.round_locks[game_id]

                await self.message_service.cleanup_game_messages(game_id)
                del self.games[game_id]

                await self.event_manager.emit(
                    GameEvent(
                        type='game_ended',
                        data={'game_id': game_id, 'channel_id': channel_id},
                    )
                )
                return True
            return False
        except Exception as e:
            logger.error(f'Error ending game: {e}')
            return False
