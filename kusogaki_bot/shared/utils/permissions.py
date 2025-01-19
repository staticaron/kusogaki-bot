from discord.ext import commands
from discord.ext.commands import CheckFailure, Context
from discord.utils import get
from typing import Callable, Any
from config import STAFF_ROLE_ID


class MissingRequiredRole(CheckFailure):
    """Exception raised when user lacks the required role or team membership."""

    pass


def has_required_permission() -> Callable[[Context], Any]:
    """Check if the user is either in a Discord Developer Portal team or has the staff role."""

    async def predicate(ctx) -> bool:
        member = ctx.author
        bot = ctx.bot

        app_info = await bot.application_info()
        if app_info.team:
            team_member_ids = [m.id for m in app_info.team.members]
            if member.id in team_member_ids:
                return True

        staff_role = get(ctx.guild.roles, id=STAFF_ROLE_ID)
        if staff_role and staff_role in member.roles:
            return True

        raise MissingRequiredRole(
            'You must be either a staff member or part of the Developer Portal team.'
        )

    return commands.check(predicate)


async def check_permission(ctx: Context) -> bool:
    """
    Check if user either has required permissions or is in the specified channel.

    Args:
        ctx: The command context

    Returns:
        bool: True if user has permission or is in allowed channel
    """
    try:
        check = has_required_permission().predicate
        return await check(ctx)
    except MissingRequiredRole:
        return False
