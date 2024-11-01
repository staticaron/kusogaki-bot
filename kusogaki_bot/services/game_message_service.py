import asyncio
import logging
from typing import List, Optional

import discord
from discord.ext import commands

from kusogaki_bot.models.round_data import RoundData
from kusogaki_bot.utils.embeds import EmbedType, get_embed

logger = logging.getLogger(__name__)


class GameMessageService:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.current_message: Optional[discord.Message] = None
        self.game_messages: List[discord.Message] = []

    async def send_game_start(
        self, ctx: commands.Context, creator: discord.User
    ) -> Optional[discord.Message]:
        """Send the game start message."""
        try:
            embed = await get_embed(
                EmbedType.NORMAL,
                'GTA Quiz Game',
                '⏰ Game starting in `15` seconds!\n\n'
                f'Starting player: {creator.mention}\n'
                'Type `kuso gtaquiz join` or `kuso gq join` to join the game!',
            )
            message = await ctx.send(embed=embed)
            self.game_messages.append(message)
            return message
        except Exception as e:
            logger.error(f'Error sending game start message: {e}', exc_info=True)
            return None

    async def run_countdown(self, message: discord.Message, game_id: str) -> bool:
        """Run the countdown timer with visual indicator."""
        try:
            for countdown in range(15, -1, -1):
                if message is None:
                    return False

                progress_bar = self._create_progress_bar(countdown)

                embed = await get_embed(
                    EmbedType.NORMAL,
                    'GTA Quiz Game',
                    f"⏰ Game starting in `{countdown}` seconds!\n"
                    f"{progress_bar}\n"
                    f"Starting player: {message.embeds[0].description.split('Starting player: ')[1].split('\n')[0]}\n"
                    "Type `kuso gtaquiz join` or `kuso gq join` to join the game!",
                )

                await message.edit(embed=embed)
                await asyncio.sleep(1)

            await self._safe_delete_message(message)
            return True
        except Exception as e:
            logger.error(f'Error running countdown: {e}', exc_info=True)
            return False

    def _create_progress_bar(self, seconds_left: int) -> str:
        """Create a visual progress bar for the countdown."""
        total_width = 20
        filled = round((seconds_left / 15) * total_width)
        empty = total_width - filled

        bar = '█' * filled + '░' * empty
        return f'`{bar}`'

    async def send_join_result(self, ctx: commands.Context, success: bool):
        """Send the result of a join attempt."""
        try:
            if not success:
                embed = await get_embed(
                    EmbedType.ERROR, 'Join Failed', 'Cannot join the game at this time!'
                )
                await ctx.send(embed=embed)
            else:
                embed = await get_embed(
                    EmbedType.NORMAL,
                    'Join Successful',
                    f'{ctx.author.mention} joined the game!',
                )
                message = await ctx.send(embed=embed)
                self.game_messages.append(message)
        except Exception as e:
            logger.error(f'Error sending join result: {e}', exc_info=True)

    async def handle_round(
        self, ctx: commands.Context, round_data: RoundData
    ) -> Optional[discord.Message]:
        """Handle displaying a round."""
        try:
            embed = await self._create_round_embed(round_data)
            await self.cleanup_current_message()

            self.current_message = await ctx.send(embed=embed)
            self.game_messages.append(self.current_message)

            for i in range(len(round_data.choices)):
                await self.current_message.add_reaction(f'{i+1}\u20e3')

            return self.current_message
        except Exception as e:
            logger.error(f'Error handling round: {e}', exc_info=True)
            return None

    async def cleanup_messages(self):
        """Clean up all game-related messages."""
        try:
            for message in self.game_messages[:]:
                await self._safe_delete_message(message)
            self.game_messages.clear()
            self.current_message = None
        except Exception as e:
            logger.error(f'Error cleaning up messages: {e}', exc_info=True)

    async def cleanup_current_message(self):
        """Clean up the current round message."""
        try:
            if self.current_message:
                await self._safe_delete_message(self.current_message)
                self.current_message = None
        except Exception as e:
            logger.error(f'Error cleaning up current message: {e}', exc_info=True)

    async def _safe_delete_message(self, message: discord.Message):
        """Safely delete a message and remove it from tracking."""
        try:
            await message.delete()
        except discord.errors.NotFound:
            logger.debug(f'Message {message.id} already deleted')
        except Exception as e:
            logger.error(f'Error deleting message: {e}', exc_info=True)
        finally:
            if message in self.game_messages:
                self.game_messages.remove(message)

    async def _create_round_embed(self, round_data: RoundData) -> discord.Embed:
        """Create an embed for a round."""
        try:
            embed = await get_embed(
                EmbedType.NORMAL,
                'Guess the GTA Scene!',
                '\n'.join(
                    f'{i+1}. {title}' for i, title in enumerate(round_data.choices)
                ),
            )
            embed.set_image(url=round_data.image_url)

            players_text = '\n'.join(
                f'<@{player_id}> - ❤️ x{player.hp}'
                for player_id, player in round_data.players.items()
            )
            embed.add_field(
                name='Players', value=players_text or 'No players', inline=False
            )

            return embed
        except Exception as e:
            logger.error(f'Error creating round embed: {e}', exc_info=True)
            return await get_embed(
                EmbedType.ERROR,
                'Error Creating Round',
                'An error occurred while creating the round.',
            )
