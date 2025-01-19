from datetime import timedelta
from typing import Dict, Tuple

import discord


class PollError(Exception):
    """Base exception for poll-related errors."""

    pass


class PollService:
    """Service class for managing polls."""

    def __init__(self):
        self.active_polls: Dict[str, Tuple[discord.Poll, discord.Message]] = {}

    def validate_options(self, options: Tuple[str, ...]) -> None:
        """
        Validate poll options.

        Args:
            options: Tuple of option strings

        Raises:
            PollError: If options are invalid
        """
        if len(options) < 2:
            raise PollError('You need to provide at least two options for the poll!')
        if len(options) > 10:
            raise PollError('You can only have up to 10 options in a poll!')

    def create_poll(
        self, question: str, duration: int, multiple: bool, options: Tuple[str, ...]
    ) -> discord.Poll:
        """
        Create a new poll.

        Args:
            question: Poll question
            duration: Duration in hours
            multiple: Whether multiple options can be selected
            options: Poll options

        Returns:
            discord.Poll: Created poll object
        """
        poll = discord.Poll(
            question=question,
            duration=timedelta(hours=duration),
            multiple=multiple,
        )
        for option in options:
            poll.add_answer(text=option)
        return poll

    def get_poll(self, question: str) -> Tuple[discord.Poll, discord.Message]:
        """
        Get a poll by its question.

        Args:
            question: Poll question

        Returns:
            Tuple[discord.Poll, discord.Message]: Poll and its message

        Raises:
            PollError: If poll not found
        """
        if question not in self.active_polls:
            raise PollError('No active poll found with that question.')
        return self.active_polls[question]

    def add_poll(
        self, question: str, poll: discord.Poll, message: discord.Message
    ) -> None:
        """Add a poll to active polls."""
        self.active_polls[question] = (poll, message)

    def remove_poll(self, question: str) -> None:
        """Remove a poll from active polls."""

        if question not in self.active_polls:
            raise PollError('No active poll found with that question.')
        return self.active_polls.pop(question)

    def list_active_polls(self) -> str:
        """Get formatted string of active polls."""
        if not self.active_polls:
            return 'There are no active polls at the moment.'
        return 'Active polls:\n' + '\n'.join(
            f'- {question}' for question in self.active_polls
        )
