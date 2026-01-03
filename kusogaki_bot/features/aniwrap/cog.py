import asyncio
import logging
import os
import pdb
import time
from io import BytesIO

import discord
from discord.ext import commands, tasks

import config
from kusogaki_bot.core import BaseCog, KusogakiBot
from kusogaki_bot.features.aniwrap.service import AniWrapService
from kusogaki_bot.shared.utils.embeds import EmbedType, get_embed

logger = logging.getLogger(__name__)


class WrapRequest:
    user_id: int = 0
    user_name: str = ''

    def __init__(self, user_id, user_name) -> None:
        self.user_id = user_id
        self.user_name = user_name


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
        userid = request.user_id
        username = request.user_name

        t0 = time.time()

        response = await self.service.generate(username)

        if response.success:
            with BytesIO(response.image_bytes) as img_binary:
                wrap_img = discord.File(img_binary, filename=f'{username}.png')

                if isinstance(self.wrap_channel, discord.abc.Messageable):
                    await self.wrap_channel.send(f'<@{userid}>', file=wrap_img)
                    logger.info(f'Wrap Generated for {username}')
                else:
                    logger.error("Can't send wrap in the WRAP CHANNEL")

                t1 = time.time()
                logger.info(f'Wrap Generated for : {username}, took : {t1 - t0}')
        else:
            error_embd, _ = await get_embed(
                EmbedType.ERROR, 'ERROR!', response.error_msg
            )

            if isinstance(self.wrap_log_channel, discord.abc.Messageable):
                await self.wrap_log_channel.send(embed=error_embd)
            else:
                logger.error("Can't send error message in the WRAP LOG CHANNEL")

            logger.error(f'ERROR OCCURRED while generating wrap for {username}')

        self.is_processing = False

    @process_wraps.before_loop
    async def init_process_wraps(self) -> None:
        await self.bot.wait_until_ready()

        self.wrap_channel = self.bot.get_channel(config.WRAP_CHANNEL_ID)
        self.wrap_log_channel = self.bot.get_channel(config.WRAP_LOG_CHANNEL_ID)

    @commands.hybrid_command(
        name='aniwrap',
        aliases=['miniwrap', 'wrap', 'alwrap'],
        description='Generate MiniWrap',
    )
    async def aniwrap(
        self,
        ctx: commands.Context,
        username: str,
    ):
        """Text Command for generating AlWrap"""
        await ctx.typing()

        await self.wrap_queue.put(WrapRequest(ctx.author.id, username))

        await ctx.reply('Generation will begin shortly!')

    @commands.hybrid_command(
        name='dummywrap',
        aliases=['dw'],
        description='Generate a dummy wrap without making API calls to kusogaki',
    )
    async def send_dummy_wrap(self, ctx: commands.Context, username: str):
        await ctx.typing()

        response = await self.service.generate(username, True)

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


async def setup(bot: commands.Bot):
    await bot.add_cog(AniWrapCog(bot))
