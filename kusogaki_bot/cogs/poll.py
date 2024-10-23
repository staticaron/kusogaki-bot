import asyncio
import logging
from datetime import timedelta
from typing import Dict, Tuple

import discord
from discord.ext import commands

logging.basicConfig(level=logging.DEBUG)


class PollError(Exception):
    """Base exception for poll-related errors."""

    pass


class PollCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.active_polls: Dict[str, Tuple[discord.Poll, discord.Message]] = {}

    @commands.command(name='poll', description='Create a new poll')
    async def create_poll(
        self,
        ctx: commands.Context,
        question: str,
        duration: int,
        multiple: bool,
        *options: str,
    ):
        """
        Create a new poll with the given question, duration, and options.

        :param ctx: The command context
        :param question: The poll question
        :param duration: The poll duration in hours
        :param multiple: Whether multiple options can be selected
        :param options: The poll options
        """
        try:
            self._validate_poll_options(options)
            poll = self._create_poll(question, duration, multiple, options)
            poll_message = await ctx.send(poll=poll)
            self.active_polls[question] = (poll, poll_message)
            self.bot.loop.create_task(
                self._remove_poll_after_expiry(question, duration)
            )
        except PollError as e:
            await ctx.send(str(e))

    @commands.command(name='endpoll', description='End an active poll')
    async def end_poll(self, ctx: commands.Context, *, question: str):
        """
        End an active poll with the given question.

        :param ctx: The command context
        :param question: The question of the poll to end
        """
        try:
            poll, _ = self._get_poll(question)
            await poll.end()
            await ctx.send(f"Poll '{question}' has been ended successfully.")
            del self.active_polls[question]
        except PollError as e:
            await ctx.send(str(e))
        except discord.HTTPException as e:
            logging.error(f'HTTP Exception when ending poll: {str(e)}')
            await ctx.send(
                'Failed to end the poll. It might have already ended or been deleted.'
            )
        except Exception as e:
            logging.error(f'Unexpected error when ending poll: {str(e)}', exc_info=True)
            await ctx.send(
                'An unexpected error occurred while ending the poll. Please check the logs for more details.'
            )

    @commands.command(name='listpolls', description='List all active polls')
    async def list_polls(self, ctx: commands.Context):
        """List all active polls."""
        polls_list = self._format_polls_list()
        await ctx.send(polls_list)

    def _validate_poll_options(self, options: Tuple[str, ...]) -> None:
        """Validate the number of options for a poll."""
        if len(options) < 2:
            raise PollError('You need to provide at least two options for the poll!')
        if len(options) > 10:
            raise PollError('You can only have up to 10 options in a poll!')

    def _create_poll(
        self, question: str, duration: int, multiple: bool, options: Tuple[str, ...]
    ) -> discord.Poll:
        """Create a new discord.Poll object."""
        poll = discord.Poll(
            question=question,
            duration=timedelta(hours=duration),
            multiple=multiple,
        )
        for option in options:
            poll.add_answer(text=option)
        return poll

    def _get_poll(self, question: str) -> Tuple[discord.Poll, discord.Message]:
        """Get an active poll by its question."""
        if question not in self.active_polls:
            raise PollError(
                "No active poll found with that question. Make sure you've typed the question exactly as it appears in the poll."
            )
        return self.active_polls[question]

    def _format_polls_list(self) -> str:
        """Format the list of active polls."""
        if not self.active_polls:
            return 'There are no active polls at the moment.'
        return 'Active polls:\n' + '\n'.join(
            f'- {question}' for question in self.active_polls
        )

    async def _remove_poll_after_expiry(self, question: str, duration: int):
        """Remove a poll from active_polls after it expires."""
        await asyncio.sleep(duration * 3600)
        self.active_polls.pop(question, None)


async def setup(bot: commands.Bot):
    await bot.add_cog(PollCog(bot))
