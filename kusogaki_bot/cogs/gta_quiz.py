import asyncio
import logging
from typing import Dict, List, Set

from discord.ext import commands

from kusogaki_bot.services.game_message_service import GameMessageService
from kusogaki_bot.services.gta_quiz_service import GTAQuizService
from kusogaki_bot.utils.base_cog import BaseCog

logger = logging.getLogger(__name__)


class GTAQuizCog(BaseCog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.quiz_service = GTAQuizService()
        self.message_service = GameMessageService(bot)
        self.answered_this_round: Dict[str, Set[int]] = {}

    @commands.group(name='gtaquiz', aliases=['gq'])
    async def gta_quiz(self, ctx: commands.Context):
        """Base command for GTA quiz game."""
        if ctx.invoked_subcommand is None:
            await ctx.send('Available commands: `start`, `join`, `stop`')

    @gta_quiz.command(name='start')
    async def start_game(self, ctx: commands.Context):
        """Start a new GTA quiz game."""
        try:
            if self.quiz_service.game_exists(ctx.channel.id):
                await ctx.send('A game is already running in this channel!')
                return

            game_id = await self.quiz_service.create_game(ctx.channel.id, ctx.author.id)
            if not game_id:
                await ctx.send('Failed to create game. Please try again.')
                return

            countdown_msg = await self.message_service.send_game_start(ctx, ctx.author)

            if await self.message_service.run_countdown(countdown_msg, game_id):
                self.quiz_service.activate_game(game_id)
                self.answered_this_round[game_id] = set()
                await self.run_game(ctx, game_id)
        except Exception as e:
            logger.error(f'Error in start_game: {e}', exc_info=True)
            await ctx.send(
                'An error occurred while starting the game. Please try again.'
            )

    @gta_quiz.command(name='join')
    async def join_game(self, ctx: commands.Context):
        """Join an ongoing game."""
        try:
            result = self.quiz_service.add_player(ctx.channel.id, ctx.author.id)
            await self.message_service.send_join_result(ctx, result)
        except Exception as e:
            logger.error(f'Error in join_game: {e}', exc_info=True)
            await ctx.send('Failed to join the game. Please try again.')

    @gta_quiz.command(name='stop')
    async def stop_game(self, ctx: commands.Context):
        """Stop the current game."""
        try:
            game_id = self.quiz_service.get_game_id_by_channel(ctx.channel.id)
            if not game_id:
                await ctx.send('No active game to stop!')
                return

            if await self.quiz_service.stop_game(game_id):
                await self.message_service.cleanup_messages()
                if game_id in self.answered_this_round:
                    del self.answered_this_round[game_id]
                await ctx.send('Game stopped!')
            else:
                await ctx.send('Failed to stop the game. Please try again.')
        except Exception as e:
            logger.error(f'Error in stop_game: {e}', exc_info=True)
            await ctx.send('An error occurred while stopping the game.')

    async def run_game(self, ctx: commands.Context, game_id: str):
        """Main game loop."""
        try:
            loading_msg = await ctx.send('🎲 Loading first round...')

            while self.quiz_service.is_game_active(game_id):
                try:
                    round_data = await self.quiz_service.prepare_round(game_id)
                    if not round_data:
                        break

                    self.answered_this_round[game_id] = set()

                    await loading_msg.edit(content='🎯 Round starting!')
                    await asyncio.sleep(1)
                    message = await self.message_service.handle_round(ctx, round_data)
                    await loading_msg.delete()

                    end_time = (
                        asyncio.get_event_loop().time()
                        + self.quiz_service.config.GUESS_TIME
                    )
                    round_start_time = asyncio.get_event_loop().time()
                    correct_answer_given = False
                    active_players = set(round_data.players.keys())
                    round_results = []
                    any_answer_given = False

                    def check_reaction(reaction, user):
                        if not self.quiz_service.is_game_active(game_id):
                            return False
                        if user.bot or user.id not in round_data.players:
                            return False
                        if user.id in self.answered_this_round.get(game_id, set()):
                            return False
                        if reaction.message.id != message.id:
                            return False
                        return str(reaction.emoji)[0].isdigit() and int(
                            str(reaction.emoji)[0]
                        ) <= len(round_data.choices)

                    while (
                        asyncio.get_event_loop().time() < end_time
                        and not correct_answer_given
                        and len(self.answered_this_round.get(game_id, set()))
                        < len(active_players)
                    ):
                        try:
                            timeout = max(
                                0.1,
                                min(
                                    end_time - asyncio.get_event_loop().time(),
                                    round_start_time
                                    + self.quiz_service.config.ROUND_TIMEOUT
                                    - asyncio.get_event_loop().time(),
                                ),
                            )

                            reaction, user = await self.bot.wait_for(
                                'reaction_add',
                                timeout=timeout,
                                check=check_reaction,
                            )

                            any_answer_given = True
                            if game_id not in self.answered_this_round:
                                self.answered_this_round[game_id] = set()

                            self.answered_this_round[game_id].add(user.id)

                            choice_idx = int(str(reaction.emoji)[0]) - 1
                            selected_answer = round_data.choices[choice_idx]

                            if selected_answer == round_data.correct_title:
                                round_results.append(
                                    {'user': user, 'correct': True, 'eliminated': False}
                                )
                                correct_answer_given = True
                            else:
                                eliminated = (
                                    await self.quiz_service.process_wrong_answer(
                                        game_id, user.id
                                    )
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
                                >= round_start_time
                                + self.quiz_service.config.ROUND_TIMEOUT
                            ):
                                await ctx.send(
                                    f'⏰ Game Over! No one answered in {self.quiz_service.config.ROUND_TIMEOUT} seconds.\n'
                                    f'The answer was: **{round_data.correct_title}**'
                                )
                                await self.quiz_service.stop_game(game_id)
                                return
                            continue

                    if any_answer_given:
                        unanswered_players = (
                            active_players
                            - self.answered_this_round.get(game_id, set())
                        )
                        for player_id in unanswered_players:
                            eliminated = await self.quiz_service.process_wrong_answer(
                                game_id, player_id
                            )
                            round_results.append(
                                {
                                    'user_id': player_id,
                                    'correct': False,
                                    'eliminated': eliminated,
                                    'timeout': True,
                                }
                            )

                        await self.display_round_results(
                            ctx, round_results, round_data.correct_title
                        )

                    await asyncio.sleep(3)
                    if not await self.quiz_service.check_game_continuation(game_id):
                        break

                    loading_msg = await ctx.send('🎲 Loading next round...')

                except Exception as e:
                    logger.error(f'Error in game round: {e}', exc_info=True)
                    await ctx.send(
                        'An error occurred during the round. Stopping the game.'
                    )
                    await self.quiz_service.stop_game(game_id)
                    break

        except Exception as e:
            logger.error(f'Error in run_game: {e}', exc_info=True)
            await ctx.send('An error occurred during the game. Stopping the game.')

        finally:
            if game_id in self.answered_this_round:
                del self.answered_this_round[game_id]
            await self.message_service.cleanup_messages()

    async def display_round_results(
        self, ctx: commands.Context, results: List[dict], correct_answer: str
    ):
        """Display all round results at once."""
        messages = []

        correct_players = [r for r in results if r.get('correct')]
        if correct_players:
            winner = correct_players[0]
            messages.append(f"🎉 {winner['user'].mention} got it right!")

        incorrect_players = [
            r for r in results if not r.get('correct') and not r.get('timeout')
        ]
        if incorrect_players:
            eliminated_players = [r for r in incorrect_players if r['eliminated']]
            survived_players = [r for r in incorrect_players if not r['eliminated']]

            if eliminated_players:
                players_text = ', '.join(
                    f"{r['user'].mention}" for r in eliminated_players
                )
                messages.append(f'❌ Eliminated: {players_text}')

            if survived_players:
                players_text = ', '.join(
                    f"{r['user'].mention}" for r in survived_players
                )
                messages.append(f'❌ Lost 1 HP: {players_text}')

        timeout_players = [r for r in results if r.get('timeout')]
        if timeout_players:
            eliminated_timeouts = [r for r in timeout_players if r['eliminated']]
            survived_timeouts = [r for r in timeout_players if not r['eliminated']]

            if eliminated_timeouts:
                players_text = ', '.join(
                    f"<@{r['user_id']}>" for r in eliminated_timeouts
                )
                messages.append(f'⏰ Eliminated for not answering: {players_text}')

            if survived_timeouts:
                players_text = ', '.join(
                    f"<@{r['user_id']}>" for r in survived_timeouts
                )
                messages.append(f'⏰ Lost 1 HP for not answering: {players_text}')

        if messages:
            results_message = '\n'.join(messages)
            await ctx.send(f'{results_message}\n\nThe answer was: **{correct_answer}**')
        else:
            await ctx.send(f'Round ended. The answer was: **{correct_answer}**')


async def setup(bot: commands.Bot):
    await bot.add_cog(GTAQuizCog(bot))
