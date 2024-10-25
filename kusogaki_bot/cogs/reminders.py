import logging
from datetime import datetime
from typing import Dict, List

import discord
from discord.ext import commands, tasks

from kusogaki_bot.data.reminder_repository import ReminderRepository
from kusogaki_bot.services.reminder_service import ReminderError, ReminderService


class RemindersCog(commands.Cog):
    """Cog for reminder-related commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.reminder_service = ReminderService()
        self.reminder_repository = ReminderRepository()
        self.reminder_service.reminders = self.reminder_repository.load()
        self.check_reminders.start()

    def cog_unload(self):
        """Clean up when cog is unloaded."""
        self.check_reminders.cancel()
        self.reminder_repository.save(self.reminder_service.reminders)

    @tasks.loop(seconds=30)
    async def check_reminders(self):
        """Check for and process due reminders."""
        current_time = datetime.now().timestamp()
        due_reminders = self.reminder_service.get_due_reminders(current_time)

        for user_id, reminder in due_reminders:
            await self._send_reminder(user_id, reminder)
            self.reminder_service.delete_reminder(user_id, 0)
            self.reminder_repository.save(self.reminder_service.reminders)

    @commands.group(name='reminder', aliases=['rem'], invoke_without_command=True)
    async def reminder(self, ctx: commands.Context):
        """Base reminder command."""
        await ctx.send('Available commands: `set`, `list`, `delete`')

    @reminder.command(name='set')
    async def set_reminder(self, ctx: commands.Context, time: str, *, message: str):
        """Set a new reminder."""
        try:
            seconds = self.reminder_service.parse_time(time)
            reminder_data = self.reminder_service.create_reminder(
                message, seconds, ctx.channel.id
            )
            self.reminder_service.add_reminder(str(ctx.author.id), reminder_data)
            self.reminder_repository.save(self.reminder_service.reminders)
            await self._send_confirmation(ctx, time, message)
        except ValueError:
            await ctx.send('Invalid time format! Use format like: 1h30m, 2d, 30m')

    @reminder.command(name='list')
    async def list_reminders(self, ctx: commands.Context):
        """List all active reminders."""
        reminders = self.reminder_service.get_user_reminders(str(ctx.author.id))
        if not reminders:
            await ctx.send('You have no active reminders!')
            return

        embed = self._create_reminders_list_embed(reminders)
        await ctx.send(embed=embed)

    @reminder.command(name='delete', aliases=['del', 'remove'])
    async def delete_reminder(self, ctx: commands.Context, index: int):
        """Delete a reminder by index."""
        try:
            self.reminder_service.delete_reminder(str(ctx.author.id), index - 1)
            self.reminder_repository.save(self.reminder_service.reminders)
            await ctx.send(f'✅ Reminder #{index} has been deleted.')
        except ReminderError as e:
            await ctx.send(str(e))

    async def _send_reminder(self, user_id: str, reminder: Dict):
        """Send a reminder to the user."""
        try:
            user = await self.bot.fetch_user(int(user_id))
            channel = self.bot.get_channel(reminder['channel_id'])

            embed = discord.Embed(
                title='⏰ Reminder!',
                description=reminder['message'],
                color=discord.Color.blue(),
            )
            embed.set_footer(
                text=f"Set {datetime.fromtimestamp(reminder['created_at']).strftime('%Y-%m-%d %H:%M:%S')}"
            )

            if channel:
                await channel.send(user.mention, embed=embed)
            else:
                await user.send(embed=embed)
        except Exception as e:
            logging.error(f'Error sending reminder: {str(e)}')

    async def _send_confirmation(self, ctx: commands.Context, time: str, message: str):
        """Send confirmation for a new reminder."""
        embed = discord.Embed(
            title='✅ Reminder Set!',
            description=f"I'll remind you about: {message}\nIn: {time}",
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed)

    def _create_reminders_list_embed(self, reminders: List[Dict]) -> discord.Embed:
        """Create embed for listing reminders."""
        embed = discord.Embed(title='Your Reminders', color=discord.Color.blue())
        for i, reminder in enumerate(reminders, 1):
            time_left = reminder['time'] - datetime.now().timestamp()
            hours = int(time_left // 3600)
            minutes = int((time_left % 3600) // 60)
            embed.add_field(
                name=f'#{i}',
                value=f"Message: {reminder['message']}\nTime left: {hours}h {minutes}m",
                inline=False,
            )
        return embed


async def setup(bot: commands.Bot):
    await bot.add_cog(RemindersCog(bot))
