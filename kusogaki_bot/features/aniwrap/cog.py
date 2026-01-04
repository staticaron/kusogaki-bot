import asyncio
import logging
import os
import pdb
import time
from io import BytesIO
from typing import Literal

import discord
from discord import Interaction, app_commands
from discord.ext import commands, tasks

import config
from kusogaki_bot.core import BaseCog, KusogakiBot
from kusogaki_bot.features.aniwrap.service import AniWrapService
from kusogaki_bot.shared.utils.embeds import EmbedType, get_embed

logger = logging.getLogger(__name__)


class WrapRequest:
    def __init__(self, token, user, wt) -> None:
        self.token = token
        self.user = user
        self.wt = wt


class AniWrapCog(BaseCog):
    service: AniWrapService = AniWrapService()

    wrap_queue = asyncio.Queue()
    is_processing: bool = False

    def __init__(self, bot: KusogakiBot):
        super().__init__(bot)
        self.bot = bot
        self.service = AniWrapService()

        self.process_wraps.start()

    async def cog_unload(self):
        self.process_wraps.cancel()

    async def send_user_message(
        self,
        user: discord.User,
        msg: str = '',
        embd: discord.Embed | None = None,
        file: discord.File | None = None,
    ) -> bool:
        try:
            if file is None:
                if embd is None:
                    await user.send(msg)
                else:
                    await user.send(msg, embed=embd)
            else:
                await user.send(
                    msg,
                    file=file,
                )
            return True
        except discord.Forbidden:
            await self.log_in_wrap_channel(f"`{user.name}` can't receive messages")
        except discord.HTTPException:
            await self.log_in_wrap_channel(
                f'`Unable to send wrap to {user.name}`, HTTPException'
            )

        return False

    async def log_in_wrap_channel(self, message, embed: discord.Embed | None = None):
        if isinstance(self.wrap_log_channel, discord.abc.Messageable):
            if embed is None:
                await self.wrap_log_channel.send(message)
            else:
                await self.wrap_log_channel.send(message, embed=embed)
        else:
            logger.error("Can't send message in WRAP LOG CHANNEL")

    @tasks.loop(seconds=5)
    async def process_wraps(self) -> None:
        if self.is_processing:
            logger.info('Already Processing a wrap')
            return
        elif self.wrap_queue.empty():
            logger.info('No Wraps to process!')
            return
        else:
            self.is_processing = True

        request = await self.wrap_queue.get()
        token = request.token
        user: discord.User = request.user
        wt = request.wt

        t0 = time.time()

        response = await self.service.generate(token, wt)

        if response.success:
            with BytesIO(response.image_bytes) as img_binary:
                # generate image using image binary data from generate()
                wrap_img = discord.File(img_binary, filename=f'{response.username}.png')

                # try sending the wrap image as a DM to the user who requested it
                success = await self.send_user_message(
                    user,
                    f'Mini Wrap Generated - {response.username}!',
                    file=wrap_img,
                )

                # if message fails to send, log the error in the log channel
                if success:
                    t1 = time.time()
                    logger.info(
                        f'Wrap Generated for : {response.username}, took : {t1 - t0}'
                    )
                else:
                    logger.info(
                        f'Wrap generation for {response.username} unsuccessful!'
                    )
                    await self.log_in_wrap_channel(
                        f'Wrap generation for {response.username} unsuccessful!'
                    )
        else:
            error_embd, _ = await get_embed(
                EmbedType.ERROR, f'ERROR! - {response.username}', response.error_msg
            )

            # let user know about the error
            success = await self.send_user_message(user, '', embd=error_embd)

            # log the error in the log channel
            await self.log_in_wrap_channel('', embed=error_embd)

            logger.error(
                f'ERROR OCCURRED while generating wrap for {response.username}'
            )

        self.is_processing = False

    @process_wraps.before_loop
    async def init_process_wraps(self) -> None:
        await self.bot.wait_until_ready()

        self.wrap_channel = self.bot.get_channel(config.WRAP_CHANNEL_ID)
        self.wrap_log_channel = self.bot.get_channel(config.WRAP_LOG_CHANNEL_ID)

    # @commands.hybrid_command(
    #    name='miniwrap',
    #    aliases=['mw', 'alwrap'],
    #    description='Generate MiniWrap',
    # )
    # async def aniwrap(self, ctx: commands.Context, username: str, wt='c'):
    #    """Text Command for generating AlWrap"""
    #    await ctx.typing()

    #    await self.wrap_queue.put(WrapRequest(token, ctx.author, wt))

    #    await ctx.reply('You will receive your wrap via DM shortly!')

    @commands.hybrid_command(
        name='dummywrap',
        aliases=['dw'],
        description='Generate a dummy wrap without making API calls to kusogaki',
    )
    async def send_dummy_wrap(self, ctx: commands.Context, username: str):
        await ctx.typing()

        response = await self.service.generate(username, 'd')

        if response.success:
            wrap_file = discord.File(f'wraps/{username}.png')

            await ctx.channel.send(file=wrap_file)
            logger.info(f'Wrap Generated for : {username}')

            os.remove(f'wraps/{username}.png')
        else:
            error_embd, _ = await get_embed(
                EmbedType.ERROR, 'ERROR!', response.error_msg
            )
            await ctx.channel.send(embed=error_embd)
            logger.error(f'ERROR OCCURRED while generating wrap for {username}')

    @app_commands.command(name='miniwrapslash', description='Generate a mini wrap!')
    @app_commands.describe(
        design='New designs uses colors from your banner/pfp to generate wraps! Old one uses your profile color',
        token='Your anilist token ( used to verify the user ). It is never stored!',
    )
    async def miniwrap(
        self, interaction: Interaction, design: Literal['New', 'Old'], token: str
    ) -> None:
        await self.wrap_queue.put(WrapRequest(token, interaction.user, design))

        await interaction.response.send_message(
            'You will receive your wrap via DM shortly!', ephemeral=True
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(AniWrapCog(bot))
