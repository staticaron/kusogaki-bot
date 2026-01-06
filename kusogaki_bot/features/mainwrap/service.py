from kusogaki_bot.features.mainwrap.replacemedia import replace_media
from kusogaki_bot.features.mainwrap.task_manager import EditTopTask
from kusogaki_bot.shared.utils.token import get_id_from_token


class EditTopService:
    def __init__(self, bot) -> None:
        self.bot = bot

    async def get_updated_image(self, task: EditTopTask):
        user_id = await get_id_from_token(task.token)
        replace_media(user_id, task.anime_urls, task.manga_urls)
