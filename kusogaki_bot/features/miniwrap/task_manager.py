import asyncio
import time
from io import BytesIO

from discord import File, User
from discord.ext import tasks

from config import WRAP_LOG_CHANNEL_ID
from kusogaki_bot.features.miniwrap.service import AniWrapService
from kusogaki_bot.shared.services.logger import logger
from kusogaki_bot.shared.utils.embeds import EmbedType, get_embed
from kusogaki_bot.shared.utils.send_dm import SendDM
from kusogaki_bot.shared.utils.send_in_log_channel import SendLogInLogChannel


class TaskManager:
    wrap_queue = asyncio.Queue()
    is_processing: bool = False

    def __init__(self, bot) -> None:
        self.bot = bot
        self.service = AniWrapService()
        self.wrap_channel_logger = SendLogInLogChannel(self.bot)
        self.send_dm = SendDM()

    @tasks.loop(seconds=5)
    async def process_wraps(self) -> None:
        """
        Runs every 5 seconds to check if there are any wrap requests in the queue
        If there are, starting working on the it while preventing any concurrent wrap generations
        """

        if self.is_processing:
            return logger.info('Already Processing a wrap')

        if self.wrap_queue.empty():
            self.process_wraps.stop()
            return logger.warning('No Wraps to process! Stopping Task')

        # block wrap processing for remaining wraps while the current one is getting processed
        self.is_processing = True

        request = await self.wrap_queue.get()
        token = request.token
        user: User = request.user
        wt = request.wt

        # timer to get wrap generation time
        t0 = time.time()

        # raw image binary data from wrap generation logic
        response = await self.service.generate(token, wt)

        if response.success:
            with BytesIO(response.image_bytes) as img_binary:
                # generate image using image binary data from generate()
                wrap_img = File(img_binary, filename=f'{response.username}.png')

                # try sending the wrap image as a DM to the user who requested it
                send_dm_response = await self.send_dm.send_user_message(
                    user,
                    f'Mini Wrap Generated - {response.username}!',
                    file=wrap_img,
                )

                # if message fails to send, log the error in the log channel
                if not send_dm_response.error:
                    t1 = time.time()
                    logger.info(
                        f'Wrap Generated for : {response.username}, took : {t1 - t0}'
                    )
                else:
                    if send_dm_response.error_msg.lower() == 'Forbidden':
                        await self.wrap_channel_logger.send_wrap_log(
                            f"`{user.name}` can't receive messages"
                        )
                    elif send_dm_response.error_msg.lower() == 'HTTPException':
                        await self.wrap_channel_logger.send_wrap_log(
                            f'`Unable to send wrap to {user.name}`, HTTPException'
                        )

                    logger.error(
                        f'Wrap generation for {response.username} unsuccessful!'
                    )

        # wrap generation failed! Log in the log channel
        else:
            error_embd, _ = await get_embed(
                EmbedType.ERROR, f'ERROR! - {response.username}', response.error_msg
            )

            # let user know about the error
            send_dm_response = await self.send_dm.send_user_message(
                user, '', embd=error_embd
            )

            # log the error in the log channel
            await self.wrap_channel_logger.send_wrap_log('', embed=error_embd)

            logger.error(
                f'ERROR OCCURRED while generating wrap for {response.username}'
            )

        # Open the wrap generation for remaining wraps
        self.is_processing = False

    @process_wraps.before_loop
    async def init_process_wraps(self) -> None:
        """Prepare Log Channels after the bot is fully loaded!"""
        await self.bot.wait_until_ready()

        self.wrap_log_channel = self.bot.get_channel(WRAP_LOG_CHANNEL_ID)
