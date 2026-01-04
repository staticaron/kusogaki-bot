from discord import Embed
from discord.abc import Messageable

from config import WRAP_LOG_CHANNEL_ID
from kusogaki_bot.shared.services.logger import logger


class SendLogInLogChannel:
    wrap_log_channel = None

    def __init__(self, bot) -> None:
        self.bot = bot

    async def send_wrap_log(self, message, embed: Embed | None = None):
        if self.wrap_log_channel is None:
            self.wrap_log_channel = self.bot.get_channel(WRAP_LOG_CHANNEL_ID)
            logger.warning('Wrap Log Channel Loaded!')

        if isinstance(self.wrap_log_channel, Messageable):
            if embed is None:
                await self.wrap_log_channel.send(message)
            else:
                await self.wrap_log_channel.send(message, embed=embed)
        else:
            logger.error("Can't send message in WRAP LOG CHANNEL")
