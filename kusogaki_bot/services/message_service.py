import logging
from typing import Callable, Dict, List, Optional, Tuple

import discord
from discord.ext import commands

from kusogaki_bot.models.round_data import RoundData
from kusogaki_bot.utils.embeds import EmbedType, get_embed

logger = logging.getLogger(__name__)


class MessageService:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.messages: Dict[str, List[discord.Message]] = {}
        self.current_round_messages: Dict[str, discord.Message] = {}

    async def handle_round(
        self, channel_id: int, game_id: str, round_data: RoundData
    ) -> Optional[discord.Message]:
        """Handle sending a new round message and cleaning up the old one."""
        try:
            if game_id in self.current_round_messages:
                try:
                    await self.current_round_messages[game_id].delete()
                except discord.NotFound:
                    # we'll assume the message was already deleted
                    pass
                except discord.HTTPException as e:
                    logger.error(f'Error deleting message: {e}')
                except Exception as e:
                    logger.error(f'Unexpected error deleting message: {e}')
                del self.current_round_messages[game_id]

            channel = self.bot.get_channel(channel_id)
            if not channel:
                return None

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

            message = await channel.send(embed=embed)

            for i in range(len(round_data.choices)):
                await message.add_reaction(f'{i+1}\u20e3')

            self.current_round_messages[game_id] = message
            if game_id not in self.messages:
                self.messages[game_id] = []
            self.messages[game_id].append(message)

            return message

        except Exception as e:
            logger.error(f'Error handling round: {e}')
            return None

    async def send_game_message(
        self, channel_id: int, game_id: str, embed: discord.Embed
    ) -> Optional[discord.Message]:
        try:
            channel = self.bot.get_channel(channel_id)
            if not channel:
                return None

            message = await channel.send(embed=embed)
            if game_id not in self.messages:
                self.messages[game_id] = []
            self.messages[game_id].append(message)
            return message
        except Exception as e:
            logger.error(f'Error sending game message: {e}')
            return None

    async def wait_for_reaction(
        self,
        message: discord.Message,
        timeout: float,
        check: Callable[[discord.Reaction, discord.User], bool],
    ) -> Tuple[discord.Reaction, discord.User]:
        return await self.bot.wait_for('reaction_add', timeout=timeout, check=check)

    async def send_timeout_message(
        self, channel_id: int, timeout: int, correct_answer: str
    ):
        try:
            channel = self.bot.get_channel(channel_id)
            if channel:
                embed = await get_embed(
                    EmbedType.WARNING,
                    'Game Over',
                    f'⏰ No one answered in {timeout} seconds.\n'
                    f'The answer was: **{correct_answer}**',
                )
                await channel.send(embed=embed)
        except Exception as e:
            logger.error(f'Error sending timeout message: {e}')

    async def send_round_results(
        self,
        channel_id: int,
        results: List[dict],
        correct_answer: str,
        is_game_over: bool = False,
        final_scores: Optional[Dict[int, int]] = None,
    ):
        try:
            channel = self.bot.get_channel(channel_id)
            if not channel:
                return

            messages = []

            correct_players = [r for r in results if r.get('correct')]
            if correct_players:
                winner = correct_players[0]
                messages.append(f"🎉 {winner['user'].mention} got it right!")

            incorrect_players = [
                r for r in results if not r.get('correct') and not r.get('timeout')
            ]
            if incorrect_players:
                eliminated = [r for r in incorrect_players if r['eliminated']]
                survived = [r for r in incorrect_players if not r['eliminated']]

                if eliminated:
                    players_text = ', '.join(f"{r['user'].mention}" for r in eliminated)
                    messages.append(f'❌ Eliminated: {players_text}')

                if survived:
                    players_text = ', '.join(f"{r['user'].mention}" for r in survived)
                    messages.append(f'❌ Lost 1 HP: {players_text}')

            timeout_players = [r for r in results if r.get('timeout')]
            if timeout_players:
                eliminated = [r for r in timeout_players if r['eliminated']]
                survived = [r for r in timeout_players if not r['eliminated']]

                if eliminated:
                    players_text = ', '.join(f"<@{r['user_id']}>" for r in eliminated)
                    messages.append(f'⏰ Eliminated for not answering: {players_text}')

                if survived:
                    players_text = ', '.join(f"<@{r['user_id']}>" for r in survived)
                    messages.append(f'⏰ Lost 1 HP for not answering: {players_text}')

            if messages:
                results_message = '\n'.join(messages)
                base_message = (
                    f'{results_message}\n\nThe answer was: **{correct_answer}**'
                )

                if is_game_over and final_scores is not None:
                    sorted_players = sorted(
                        final_scores.items(),
                        key=lambda x: (x[1]['correct'], x[1]['hp']),
                        reverse=True,
                    )

                    scores_text = '\n'.join(
                        [
                            f"<@{player_id}> - ✨ {scores['correct']} correct | ❤️ x{scores['hp']}"
                            for player_id, scores in sorted_players
                        ]
                    )

                    game_over_msg = (
                        f'\n\n🏆 Game Over!\n\n' f'Final Scores:\n{scores_text}'
                    )
                    base_message += game_over_msg

                embed = await get_embed(
                    EmbedType.NORMAL,
                    'Round Results',
                    base_message,
                )
                await channel.send(embed=embed)
            else:
                base_message = f'The answer was: **{correct_answer}**'
                if is_game_over and final_scores is not None:
                    sorted_players = sorted(
                        final_scores.items(),
                        key=lambda x: (x[1]['correct'], x[1]['hp']),
                        reverse=True,
                    )

                    scores_text = '\n'.join(
                        [
                            f"<@{player_id}> - ✨ {scores['correct']} correct | ❤️ x{scores['hp']}"
                            for player_id, scores in sorted_players
                        ]
                    )

                    game_over_msg = (
                        f'\n\n🏆 Game Over!\n\n' f'Final Scores:\n{scores_text}'
                    )
                    base_message += game_over_msg

                embed = await get_embed(
                    EmbedType.NORMAL,
                    'Round Ended',
                    base_message,
                )
                await channel.send(embed=embed)

        except Exception as e:
            logger.error(f'Error sending round results: {e}')

    async def cleanup_game_messages(self, game_id: str):
        """Clean up all game-related messages."""
        try:
            if game_id in self.messages:
                messages = self.messages[game_id]
                if len(messages) == 1:
                    await messages[0].delete()
                else:
                    channel = messages[0].channel
                    await channel.delete_messages(messages)
                del self.messages[game_id]

            if game_id in self.current_round_messages:
                del self.current_round_messages[game_id]

        except Exception as e:
            logger.error(f'Error cleaning up game messages: {e}')
