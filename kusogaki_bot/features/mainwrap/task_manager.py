from asyncio import Queue

from discord.ext import tasks

from kusogaki_bot.features.mainwrap.replacemedia import replace_media
from kusogaki_bot.shared.utils.token import get_id_from_token


class EditTopTask:
    token: str = ''
    anime_urls = ()
    manga_urls = ()

    def __init__(self, token, anime_urls, manga_urls) -> None:
        self.token = token
        self.anime_urls = anime_urls
        self.manga_urls = manga_urls


class EditTopTaskManager:
    edit_top_tasks = Queue()
    is_processing = False

    def __init__(self, bot) -> None:
        self.bot = bot

    @tasks.loop(seconds=5)
    async def process_edit_top(self) -> None:
        if self.edit_top_tasks.empty():
            self.process_edit_top.stop()
            return

        if self.is_processing:
            return

        edit_top_task = await self.edit_top_tasks.get()

        user_id = await get_id_from_token(edit_top_task.token)

        await replace_media(
            user_id,
            anime_images=edit_top_task.anime_urls,
            manga_images=edit_top_task.manga_urls,
        )
