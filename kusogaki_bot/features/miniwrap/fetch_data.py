import logging

import aiohttp

import config
from kusogaki_bot.features.miniwrap.query import user_query
from kusogaki_bot.shared.utils.token import get_id_from_token

logger = logging.getLogger(__name__)


class UserData:
    error: bool = False
    error_msg: str = ''
    name: str = ''
    anime_count: str = '0'
    anime_eps: str = '0'
    anime_mean_score: str = '-'
    anime_img_url: str = ''
    manga_count: str = '0'
    manga_chaps: str = '0'
    manga_mean_score: str = '-'
    manga_img_url: str = ''
    profile_color: str = '#D777CA'
    profile_pic_url: str = ''
    banner_url: str = ''

    def __init__(self, error: bool = False, error_msg: str = ''):
        self.error = error
        self.error_msg = error_msg


async def get_user_id_from_username(username: str) -> str:
    """Hit the anilist api to get userId from username"""

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=config.ANILIST_BASE or '',
                json={'query': user_query, 'variables': {'username': username}},
            ) as response:
                response_json = await response.json()

    except Exception:
        return ''

    data = response_json.get('data', {}).get('User', None)
    if data is None:
        return ''

    return data.get('id', '')


async def fetch_user_data(token: str) -> UserData:
    """Fetch user from kusogaki api using username"""

    user_data: UserData = UserData()

    token_response = await get_id_from_token(token)

    if token_response.error:
        return UserData(True, token_response.error_msg)

    user_id = token_response.user_id

    if user_id == '' or user_id == 0:
        user_data.error = True
        user_data.error_msg = token_response.error_msg
        return user_data

    url = f'https://kusogaki.co/api/alwrap/statistics/{user_id}'
    params = {'wrapYear': 2025}
    headers = {'Authorization': f'Bearer {config.KUSOGAKI_TOKEN}'}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url, params=params, headers=headers) as response:
                if response.status == 204:
                    user_data.error = True
                    user_data.error_msg = '204 No Content | Wrap is not available!\n1. Make sure you have applied for your wrap @ https://kusogaki.co/alwrap \n2. Wait until you receive your wrap on anilist!'
                    return user_data

                response.raise_for_status()
                data = await response.json(content_type=None)

                user_data.name = data['Username']
                user_data.anime_count = data['AnimeCompleted']
                user_data.anime_eps = data['EpisodesWatched']
                anime_mean_score = (
                    str(round(data['AnimeMeanScore'], 1)) + '%'
                    if data['AnimeMeanScore'] is not None
                    else '-'
                )
                user_data.anime_mean_score = anime_mean_score
                user_data.anime_img_url = data.get('TopAnime', '')[0].get(
                    'ImageUrl', ''
                )

                user_data.manga_count = data['MangaCompleted']
                user_data.manga_chaps = data['ChaptersRead']
                manga_mean_score = (
                    str(round(data['MangaMeanScore'], 1)) + '%'
                    if data['MangaMeanScore'] is not None
                    else '-'
                )
                user_data.manga_mean_score = manga_mean_score
                user_data.manga_img_url = data.get('TopManga', '')[0].get(
                    'ImageUrl', ''
                )

                user_data.profile_color = data['TextColor']

                user_data.profile_pic_url = (
                    data['ProfileImageUrl']
                    if data['ProfileImageUrl'] is not None
                    else ''
                )
                user_data.banner_url = (
                    data['BannerImageUrl'] if data['BannerImageUrl'] is not None else ''
                )

                return user_data

    except aiohttp.ClientResponseError as http_err:
        user_data.error = True
        user_data.error_msg = f'HTTP error occurred: ```{http_err}```'
        return user_data

    except Exception as err:
        user_data.error = True
        user_data.error_msg = f'Error occurred: ```{err}```'
        return user_data


async def fetch_demo_user_data(username: str) -> UserData:
    """Retrun some random data for testing"""

    user_data = UserData()

    user_data.name = username
    user_data.anime_count = '98'
    user_data.anime_eps = '1020'
    user_data.anime_mean_score = '78.69849598'
    user_data.anime_img_url = ''
    user_data.manga_count = '29'
    user_data.manga_chaps = '345'
    user_data.manga_mean_score = '85.845940'
    user_data.manga_img_url = 'https://s4.anilist.co/file/anilistcdn/media/manga/cover/medium/bx188781-Dg2ZgRhzIZ8X.jpg'

    user_data.profile_color = '#3399FF'
    user_data.profile_pic_url = 'https://s4.anilist.co/file/anilistcdn/user/avatar/large/b423414-8lJtz55b92ny.png'
    user_data.banner_url = (
        'https://s4.anilist.co/file/anilistcdn/user/banner/b5864288-tVoidJhllJva.jpg'
    )

    return user_data
