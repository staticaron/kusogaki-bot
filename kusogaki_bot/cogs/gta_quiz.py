import asyncio
import logging
from typing import Dict, Optional

import discord
from discord.ext import commands

from kusogaki_bot.models.game_config import GameConfig
from kusogaki_bot.services.anilist_service import AniListService
from kusogaki_bot.services.event_manager import GameEventManager
from kusogaki_bot.services.game_manager import GameManager
from kusogaki_bot.services.message_service import MessageService
from kusogaki_bot.services.player_service import PlayerService
from kusogaki_bot.services.quiz_round_service import QuizRoundService
from kusogaki_bot.utils.embeds import EmbedType, get_embed

logger = logging.getLogger(__name__)


class GTAQuizCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.config = GameConfig()
        self.event_manager = GameEventManager()
        self.anilist_service = AniListService()
        self.message_service = MessageService(bot)
        self.quiz_round_service = QuizRoundService(
            self.anilist_service, self.event_manager
        )
        self.player_service = PlayerService(self.event_manager)

        self.game_manager = GameManager(
            self.event_manager,
            self.quiz_round_service,
            self.player_service,
            self.message_service,
            self.config,
        )

        self.active_countdowns: Dict[str, asyncio.Task] = {}

        self.setup_event_handlers()

        self.init_task = asyncio.create_task(self.initialize_services())

    async def initialize_services(self):
        """Initialize required services."""
        try:
            await self.anilist_service.initialize()
        except Exception as e:
            logger.error(f'Failed to initialize services: {e}')

    def setup_event_handlers(self):
        """Set up all event handlers for the game."""
        self.event_manager.subscribe('game_created', self.handle_game_created)
        self.event_manager.subscribe('game_started', self.handle_game_started)
        self.event_manager.subscribe('answer_received', self.handle_answer_received)
        self.event_manager.subscribe('game_ended', self.handle_game_ended)
        self.event_manager.subscribe('player_joined', self.handle_player_joined)
        self.event_manager.subscribe('player_eliminated', self.handle_player_eliminated)
        self.event_manager.subscribe('round_ended', self.handle_round_ended)

    @commands.group(name='gtaquiz', aliases=['gq'])
    async def gta_quiz(self, ctx: commands.Context):
        """Base command for GTA quiz game."""
        if ctx.invoked_subcommand is None:
            await ctx.send('Available commands: `start`, `join`, `stop`')

    @gta_quiz.command(name='start')
    async def start_game(self, ctx: commands.Context):
        """Start a new GTA quiz game."""
        try:
            for game_state in self.game_manager.games.values():
                if game_state.channel_id == ctx.channel.id:
                    await ctx.send('A game is already running in this channel!')
                    return

            game_id = await self.game_manager.create_game(ctx.channel.id, ctx.author.id)
            if not game_id:
                await ctx.send('Failed to create game. Please try again.')
                return

            countdown_msg = await self.send_game_start(ctx, ctx.author)
            self.active_countdowns[game_id] = asyncio.create_task(
                self.run_countdown(game_id, countdown_msg)
            )

        except Exception as e:
            logger.error(f'Error starting game: {e}')
            await ctx.send('An error occurred while starting the game.')

    @gta_quiz.command(name='join')
    async def join_game(self, ctx: commands.Context):
        """Join an ongoing game."""
        try:
            for game_id, game_state in self.game_manager.games.items():
                if game_state.channel_id == ctx.channel.id:
                    if game_state.is_active:
                        await ctx.send('Cannot join an active game!')
                        return

                    success = await self.player_service.add_player(
                        {'id': game_id, 'players': game_state.players},
                        ctx.author.id,
                        self.config.STARTING_HP,
                    )

                    if success:
                        embed = await get_embed(
                            EmbedType.NORMAL,
                            'Join Successful',
                            f'{ctx.author.mention} joined the game!',
                        )
                    else:
                        embed = await get_embed(
                            EmbedType.ERROR,
                            'Join Failed',
                            'You are already in the game!',
                        )

                    await ctx.send(embed=embed)
                    return

            await ctx.send('No game available to join!')

        except Exception as e:
            logger.error(f'Error joining game: {e}')
            await ctx.send('Failed to join the game. Please try again.')

    @gta_quiz.command(name='stop')
    async def stop_game(self, ctx: commands.Context):
        """Stop the current game."""
        try:
            for game_id, game_state in self.game_manager.games.items():
                if game_state.channel_id == ctx.channel.id:
                    if game_id in self.active_countdowns:
                        self.active_countdowns[game_id].cancel()
                        del self.active_countdowns[game_id]

                    await self.game_manager.end_game(game_id)
                    await ctx.send('Game stopped!')
                    return

            await ctx.send('No active game to stop!')

        except Exception as e:
            logger.error(f'Error stopping game: {e}')
            await ctx.send('An error occurred while stopping the game.')

    async def send_game_start(
        self, ctx: commands.Context, creator: discord.User
    ) -> Optional[discord.Message]:
        """Send the game start message."""
        try:
            embed = await get_embed(
                EmbedType.NORMAL,
                'GTA Quiz Game',
                f'⏰ Game starting in `{self.config.COUNTDOWN_TIME}` seconds!\n\n'
                f'Starting player: {creator.mention}\n'
                'Type `kuso gtaquiz join` or `kuso gq join` to join the game!',
            )
            return await self.message_service.send_game_message(
                ctx.channel.id, ctx.message.id, embed
            )
        except Exception as e:
            logger.error(f'Error sending game start: {e}')
            return None

    async def run_countdown(self, game_id: str, message: discord.Message) -> None:
        """Run the countdown timer with visual indicator."""
        try:
            for countdown in range(self.config.COUNTDOWN_TIME, -1, -1):
                if message is None or not message.id:
                    return

                progress_bar = self._create_progress_bar(countdown)

                current_desc = message.embeds[0].description
                starting_player = current_desc.split('Starting player: ')[1].split(
                    '\n'
                )[0]

                embed = message.embeds[0]
                embed.description = (
                    f'⏰ Game starting in `{countdown}` seconds!\n'
                    f'{progress_bar}\n'
                    f'Starting player: {starting_player}\n'
                    'Type `kuso gtaquiz join` or `kuso gq join` to join the game!'
                )

                await message.edit(embed=embed)
                await asyncio.sleep(1)

            await self.game_manager.start_game(game_id)

        except asyncio.CancelledError:
            logger.info(f'Countdown cancelled for game {game_id}')
        except Exception as e:
            logger.error(f'Error in countdown: {e}')
        finally:
            if game_id in self.active_countdowns:
                del self.active_countdowns[game_id]

    def _create_progress_bar(self, seconds_left: int) -> str:
        """Create a visual progress bar for the countdown."""
        total_width = 20
        filled = round((seconds_left / self.config.COUNTDOWN_TIME) * total_width)
        empty = total_width - filled
        return f'`{"█" * filled}{"░" * empty}`'

    async def handle_game_created(self, data: dict):
        """Handle game creation event."""
        logger.info(f"Game created: {data['game_id']}")

    async def handle_game_started(self, data: dict):
        """Handle game start event."""
        try:
            game_id = data['game_id']
            game_state = self.game_manager.games.get(game_id)

            if not game_state:
                return

            round_data = await self.quiz_round_service.prepare_round(
                game_id, game_state.players
            )

            if not round_data:
                await self.game_manager.end_game(game_id)
                channel = self.bot.get_channel(game_state.channel_id)
                if channel:
                    await channel.send('Failed to prepare game round. Ending game.')
                return

        except Exception as e:
            logger.error(f'Error handling game start: {e}')

    async def handle_answer_received(self, data: dict):
        """Handle received answer event."""
        try:
            game_id = data['game_id']
            player_id = data['player_id']
            answer = data['answer']

            game_state = self.game_manager.games.get(game_id)
            if not game_state:
                return

            round_data = self.quiz_round_service.current_rounds.get(game_id)
            if not round_data:
                return

            choice_idx = int(str(answer.emoji)[0]) - 1
            selected_answer = round_data.choices[choice_idx]

            if selected_answer == round_data.correct_title:
                await self.handle_correct_answer(game_id, player_id)
            else:
                await self.handle_wrong_answer(game_id, player_id)

        except Exception as e:
            logger.error(f'Error handling answer: {e}')

    async def handle_correct_answer(self, game_id: str, player_id: int):
        """Handle correct answer from player."""
        try:
            game_state = self.game_manager.games.get(game_id)
            if not game_state:
                return

            channel = self.bot.get_channel(game_state.channel_id)
            if not channel:
                return

            round_data = self.quiz_round_service.current_rounds.get(game_id)
            if not round_data:
                return

            await channel.send(
                f'🎉 <@{player_id}> got it right!\n'
                f'The answer was: **{round_data.correct_title}**'
            )

            await asyncio.sleep(3)
            await self.quiz_round_service.prepare_round(game_id, game_state.players)

        except Exception as e:
            logger.error(f'Error handling correct answer: {e}')

    async def handle_wrong_answer(self, game_id: str, player_id: int):
        """Handle wrong answer from player."""
        try:
            eliminated = await self.game_manager.process_wrong_answer(
                game_id, player_id
            )

            game_state = self.game_manager.games.get(game_id)
            if not game_state:
                return

            channel = self.bot.get_channel(game_state.channel_id)
            if not channel:
                return

            if eliminated:
                await channel.send(f'❌ <@{player_id}> has been eliminated!')

                if not await self.game_manager.check_game_continuation(game_id):
                    await self.game_manager.end_game(game_id)
            else:
                await channel.send(f'❌ <@{player_id}> lost 1 HP!')

        except Exception as e:
            logger.error(f'Error handling wrong answer: {e}')

    async def handle_game_ended(self, data: dict):
        """Handle game end event."""
        try:
            channel_id = data['channel_id']
            game_id = data['game_id']
            channel = self.bot.get_channel(channel_id)

            if channel:
                await channel.send('Game Over!')

            if game_id in self.active_countdowns:
                self.active_countdowns[game_id].cancel()
                del self.active_countdowns[game_id]

            await self.message_service.cleanup_game_messages(game_id)

            if not self.game_manager.games and getattr(
                self, '_is_shutting_down', False
            ):
                await self.anilist_service.close()

        except Exception as e:
            logger.error(f'Error handling game end: {e}')

    async def handle_player_joined(self, data: dict):
        """Handle player join event."""
        logger.info(f"Player {data['player_id']} joined game {data['game_id']}")

    async def handle_player_eliminated(self, data: dict):
        """Handle player elimination event."""
        logger.info(
            f"Player {data['player_id']} eliminated from game {data['game_id']}"
        )

    async def handle_round_ended(self, data: dict):
        """Handle round end event."""
        logger.info(f"Round ended for game {data['game_id']}")

    async def cog_unload(self):
        """Cleanup when the cog is unloaded."""
        try:
            if hasattr(self, 'init_task'):
                self.init_task.cancel()

            for task in self.active_countdowns.values():
                task.cancel()
            self.active_countdowns.clear()

            for game_id in list(self.game_manager.games.keys()):
                await self.game_manager.end_game(game_id)

            await self.anilist_service.close()

        except Exception as e:
            logger.error(f'Error during cog cleanup: {e}')


async def setup(bot: commands.Bot):
    await bot.add_cog(GTAQuizCog(bot))
