import logging
from datetime import datetime
from typing import Dict

import discord
from discord.ext import commands, tasks

from kusogaki_bot.data.scheduled_thread_repository import ScheduledThreadRepository
from kusogaki_bot.services.scheduled_thread_service import (
    ScheduledThreadService,
    ThreadError,
)
from kusogaki_bot.utils.base_cog import BaseCog
from kusogaki_bot.utils.embeds import EmbedType, get_embed


class ScheduledThreadsCog(BaseCog):
    """Cog for scheduled private thread commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.thread_service = ScheduledThreadService()
        self.thread_repository = ScheduledThreadRepository()
        self.thread_service.scheduled_threads = self.thread_repository.load()
        self.check_scheduled_threads.start()

    def cog_unload(self):
        """Clean up when cog is unloaded."""
        self.check_scheduled_threads.cancel()
        self.thread_repository.save(self.thread_service.scheduled_threads)

    @tasks.loop(seconds=30)
    async def check_scheduled_threads(self):
        """Check for and process due thread creations."""
        current_time = datetime.now().timestamp()
        due_threads = self.thread_service.get_due_threads(current_time)

        for thread_data in due_threads:
            try:
                await self._create_private_thread(thread_data)
            except Exception as e:
                logging.error(f'Error processing scheduled thread: {str(e)}')
            finally:
                if 'id' in thread_data:
                    try:
                        self.thread_service.delete_thread(thread_data['id'])
                    except ThreadError:
                        logging.warning(
                            f"Failed to delete thread {thread_data['id']}, may already be deleted"
                        )

                self.thread_repository.save(self.thread_service.scheduled_threads)

    async def _create_private_thread(self, thread_data: Dict):
        """Create a private thread and set permissions."""
        try:
            channel = self.bot.get_channel(thread_data['channel_id'])
            if not channel:
                logging.error(f"Channel {thread_data['channel_id']} not found")
                return

            thread = await channel.create_thread(
                name=thread_data['name'],
                type=discord.ChannelType.private_thread,
            )

            role = channel.guild.get_role(thread_data['role_id'])
            if role:
                for member in role.members:
                    try:
                        await thread.add_user(member)
                    except Exception as e:
                        logging.error(
                            f'Error adding member {member.id} to thread: {str(e)}'
                        )
                        continue

            if thread_data.get('message'):
                embed = await get_embed(
                    EmbedType.INFORMATION,
                    'Scheduled Thread Created',
                    thread_data['message'],
                )
                await thread.send(embed=embed)

        except Exception as e:
            logging.error(f'Error creating scheduled thread: {str(e)}')

    @commands.group(name='thread', invoke_without_command=True)
    @commands.has_permissions(manage_threads=True)
    async def thread(self, ctx: commands.Context):
        """Base thread command."""
        await ctx.send('Available commands: `create`, `schedule`, `list`, `delete`')

    @thread.command(name='create')
    @commands.has_permissions(manage_threads=True)
    async def create_thread(
        self,
        ctx: commands.Context,
        role: discord.Role,
        name: str,
        *,
        message: str = None,
    ):
        """Create a private thread immediately."""
        try:
            thread_data = {
                'name': name,
                'channel_id': ctx.channel.id,
                'role_id': role.id,
                'message': message,
            }

            await self._create_private_thread(thread_data)

            embed = await get_embed(
                EmbedType.NORMAL,
                '✅ Thread Created!',
                f'Created thread: {name}\n'
                f'In channel: #{ctx.channel.name}\n'
                f'For role: {role.name}',
            )
            await ctx.send(embed=embed)

        except Exception as e:
            error_embed = await get_embed(
                EmbedType.ERROR, '❌ Error', f'Failed to create thread: {str(e)}'
            )
            await ctx.send(embed=error_embed)

    @thread.command(name='schedule')
    @commands.has_permissions(manage_threads=True)
    async def schedule_thread(
        self,
        ctx: commands.Context,
        role: discord.Role,
        time: str,
        name: str,
        *,
        message: str = None,
    ):
        """Schedule a private thread creation."""
        try:
            seconds = self.thread_service.parse_time(time)
            thread_data = self.thread_service.create_thread_data(
                name=name,
                channel_id=ctx.channel.id,
                role_id=role.id,
                seconds=seconds,
                message=message,
            )
            self.thread_service.add_thread(thread_data)
            self.thread_repository.save(self.thread_service.scheduled_threads)

            await self._send_confirmation(ctx, name, time, role.name)
        except ValueError:
            await ctx.send('Invalid time format! Use format like: 1h30m, 2d, 30m')

    @thread.command(name='list')
    @commands.has_permissions(manage_threads=True)
    async def list_threads(self, ctx: commands.Context):
        """List all scheduled threads."""
        threads = self.thread_service.get_all_threads()
        if not threads:
            await ctx.send('No scheduled threads!')
            return

        embed = await self._create_threads_list_embed(threads)
        await ctx.send(embed=embed)

    @thread.command(name='delete', aliases=['del', 'remove'])
    @commands.has_permissions(manage_threads=True)
    async def delete_thread(self, ctx: commands.Context, thread_id: str):
        """Delete a scheduled thread by ID."""
        try:
            self.thread_service.delete_thread(thread_id)
            self.thread_repository.save(self.thread_service.scheduled_threads)
            await ctx.send('✅ Scheduled thread has been deleted.')
        except ThreadError as e:
            await ctx.send(str(e))

    async def _send_confirmation(
        self, ctx: commands.Context, name: str, time: str, role_name: str
    ):
        """Send confirmation for a new scheduled thread."""
        embed = await get_embed(
            EmbedType.NORMAL,
            '✅ Thread Scheduled!',
            f"I'll create thread: {name}\n" f'For role: {role_name}\n' f'In: {time}',
        )
        await ctx.send(embed=embed)

    async def _create_threads_list_embed(self, threads: Dict) -> discord.Embed:
        """Create embed for listing scheduled threads."""
        embed = await get_embed(EmbedType.INFORMATION, 'Scheduled Threads', '')

        for thread_id, thread in threads.items():
            time_left = thread['time'] - datetime.now().timestamp()
            hours = int(time_left // 3600)
            minutes = int((time_left % 3600) // 60)

            channel = self.bot.get_channel(thread['channel_id'])
            channel_name = channel.name if channel else 'Unknown channel'

            embed.add_field(
                name=f'ID: {thread_id}',
                value=(
                    f"Name: {thread['name']}\n"
                    f"Channel: #{channel_name}\n"
                    f"Time left: {hours}h {minutes}m"
                ),
                inline=False,
            )
        return embed


async def setup(bot: commands.Bot):
    await bot.add_cog(ScheduledThreadsCog(bot))
