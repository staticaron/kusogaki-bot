import json
import logging
from datetime import datetime
from typing import Dict, List

import discord
from discord.ext import commands, tasks

logging.basicConfig(level=logging.DEBUG)


class ReminderError(Exception):
    """Base exception for reminder-related errors."""

    pass


class Reminders(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.reminders: Dict[str, List[Dict]] = {}
        self.check_reminders.start()
        self.load_reminders()

    def cog_unload(self) -> None:
        """Clean up resources when cog is unloaded."""
        self.check_reminders.cancel()
        self.save_reminders()

    def load_reminders(self) -> None:
        """Load reminders from JSON file."""
        try:
            with open('reminders.json', 'r') as f:
                self.reminders = json.load(f)
        except FileNotFoundError:
            self.reminders = {}
        except json.JSONDecodeError as e:
            logging.error(f'Error decoding reminders.json: {str(e)}')
            self.reminders = {}

    def save_reminders(self) -> None:
        """Save reminders to JSON file."""
        try:
            with open('reminders.json', 'w') as f:
                json.dump(self.reminders, f)
        except IOError as e:
            logging.error(f'Error saving reminders: {str(e)}')

    @tasks.loop(seconds=30)
    async def check_reminders(self) -> None:
        """Check for and process due reminders every 30 seconds."""
        current_time = datetime.now().timestamp()
        for user_id in list(self.reminders.keys()):
            await self._process_user_reminders(user_id, current_time)

    async def _process_user_reminders(self, user_id: str, current_time: float) -> None:
        """Process all reminders for a specific user."""
        user_reminders = self.reminders[user_id]
        for reminder in user_reminders[:]:
            if current_time >= reminder['time']:
                await self._send_reminder(user_id, reminder)
                user_reminders.remove(reminder)
                if not user_reminders:
                    del self.reminders[user_id]
                self.save_reminders()

    async def _send_reminder(self, user_id: str, reminder: Dict) -> None:
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

    @commands.group(name='reminder', aliases=['rem'], invoke_without_command=True)
    async def reminder(self, ctx: commands.Context) -> None:
        """Base reminder command. Use subcommands to manage reminders."""
        await ctx.send(
            'Available commands: `set`, `list`, `delete`\nUse `!help reminder` for more information.'
        )

    @reminder.command(name='set')
    async def set_reminder(
        self, ctx: commands.Context, time: str, *, message: str
    ) -> None:
        """
        Set a reminder with the specified time and message.

        :param ctx: The command context
        :param time: Time duration (format: 1h30m, 2d, 30m, etc.)
        :param message: The reminder message
        """
        try:
            seconds = self._parse_time(time)
            reminder_data = self._create_reminder_data(message, seconds, ctx.channel.id)
            await self._add_reminder(ctx.author.id, reminder_data)
            await self._send_confirmation(ctx, time, message)
        except ValueError:
            await ctx.send('Invalid time format! Use format like: 1h30m, 2d, 30m')
        except Exception as e:
            logging.error(f'Error setting reminder: {str(e)}')
            await ctx.send('An error occurred while setting the reminder.')

    @reminder.command(name='list')
    async def list_reminders(self, ctx: commands.Context) -> None:
        """List all active reminders for the user."""
        user_reminders = self.reminders.get(str(ctx.author.id), [])
        if not user_reminders:
            await ctx.send('You have no active reminders!')
            return

        embed = self._create_reminders_list_embed(user_reminders)
        await ctx.send(embed=embed)

    @reminder.command(name='delete', aliases=['del', 'remove'])
    async def delete_reminder(self, ctx: commands.Context, index: int) -> None:
        """
        Delete a reminder by its index number.

        :param ctx: The command context
        :param index: The index of the reminder to delete
        """
        try:
            await self._delete_reminder(ctx.author.id, index)
            await ctx.send(f'✅ Reminder #{index} has been deleted.')
        except ReminderError as e:
            await ctx.send(str(e))
        except Exception as e:
            logging.error(f'Error deleting reminder: {str(e)}')
            await ctx.send('An error occurred while deleting the reminder.')

    def _parse_time(self, time_str: str) -> int:
        """
        Parse time string into seconds.

        :param time_str: Time string in format like 1h30m, 2d, 30m
        :return: Total seconds
        """
        seconds = 0
        time_str = time_str.lower()

        if 'd' in time_str:
            days, time_str = time_str.split('d')
            seconds += int(days) * 86400
        if 'h' in time_str:
            hours, time_str = time_str.split('h')
            seconds += int(hours) * 3600
        if 'm' in time_str:
            minutes, time_str = time_str.split('m')
            seconds += int(minutes) * 60

        if seconds == 0:
            raise ValueError('Invalid time format')

        return seconds

    def _create_reminder_data(
        self, message: str, seconds: int, channel_id: int
    ) -> Dict:
        """Create reminder data dictionary."""
        current_time = datetime.now().timestamp()
        return {
            'message': message,
            'time': current_time + seconds,
            'created_at': current_time,
            'channel_id': channel_id,
        }

    async def _add_reminder(self, user_id: int, reminder_data: Dict) -> None:
        """Add a reminder to the user's reminders list."""
        user_id_str = str(user_id)
        if user_id_str not in self.reminders:
            self.reminders[user_id_str] = []
        self.reminders[user_id_str].append(reminder_data)
        self.save_reminders()

    async def _send_confirmation(
        self, ctx: commands.Context, time: str, message: str
    ) -> None:
        """Send confirmation message for a new reminder."""
        embed = discord.Embed(
            title='✅ Reminder Set!',
            description=f"I'll remind you about: {message}\nIn: {time}",
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed)

    def _create_reminders_list_embed(self, user_reminders: List[Dict]) -> discord.Embed:
        """Create embed for listing reminders."""
        embed = discord.Embed(title='Your Reminders', color=discord.Color.blue())
        for i, reminder in enumerate(user_reminders, 1):
            time_left = reminder['time'] - datetime.now().timestamp()
            hours = int(time_left // 3600)
            minutes = int((time_left % 3600) // 60)
            embed.add_field(
                name=f'#{i}',
                value=f"Message: {reminder['message']}\nTime left: {hours}h {minutes}m",
                inline=False,
            )
        return embed

    async def _delete_reminder(self, user_id: int, index: int) -> None:
        """Delete a reminder by its index."""
        user_id_str = str(user_id)
        user_reminders = self.reminders.get(user_id_str, [])

        if not user_reminders:
            raise ReminderError('You have no active reminders!')

        try:
            index = index - 1
            if 0 <= index < len(user_reminders):
                user_reminders.pop(index)
                if not user_reminders:
                    del self.reminders[user_id_str]
                self.save_reminders()
            else:
                raise ReminderError('Invalid reminder index!')
        except ValueError:
            raise ReminderError('Please provide a valid number!')


async def setup(bot: commands.Bot) -> None:
    """Set up the Reminders cog."""
    await bot.add_cog(Reminders(bot))
