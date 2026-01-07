from asyncio import Queue

from discord import Member, User
from discord.ext import tasks

from kusogaki_bot.features.mainwrap.replacemedia import replace_media
from kusogaki_bot.shared.utils.send_dm import SendDM
from kusogaki_bot.shared.utils.token import get_id_from_token


class EditTopTask:
    token: str = ''
    anime_urls = ()
    manga_urls = ()

    def __init__(self, token, anime_urls, manga_urls, user: User | Member) -> None:
        self.token = token
        self.anime_urls = anime_urls
        self.manga_urls = manga_urls
        self.user = user


class EditTopTaskManager:
    edit_top_tasks = Queue()
    is_processing = False

    def __init__(self, bot) -> None:
        self.bot = bot
        self.send_dm = SendDM()

    @tasks.loop(seconds=5)
    async def process_edit_top(self) -> None:
        if self.edit_top_tasks.empty():
            self.process_edit_top.stop()
            return

        if self.is_processing:
            return

        self.is_processing = True
        edit_top_task = await self.edit_top_tasks.get()

        try:
            token_response = await get_id_from_token(edit_top_task.token)
            if token_response.error:
                return

            user_id = token_response.user_id

            result = await replace_media(
                user_id,
                anime_images=edit_top_task.anime_urls,
                manga_images=edit_top_task.manga_urls,
            )

            if result and edit_top_task.user:
                wrap_url = f'https://kusogaki.co/images/wraps/{user_id}.png'
                await self.send_dm.send_user_message(
                    edit_top_task.user,
                    f'Your wrap has been updated! View it here: {wrap_url}',
                )
        except Exception:
            pass
        finally:
            self.is_processing = False
