import requests

import config
from kusogaki_bot.features.aniwrap.query import user_query


class UserData:
    error: bool = False
    error_msg: str = ''
    name: str = ''
    anime_count: int = 0
    anime_eps: int = 0
    anime_mean_score: float = 0.0
    manga_count: int = 0
    manga_chaps: int = 0
    manga_mean_score: float = 0.0


def get_user_id_from_username(username: str) -> str:
    """Hit the anilist api to get userId from username"""

    try:
        response = requests.post(
            url=config.ANILIST_BASE or '',
            json={'query': user_query, 'variables': {'username': username}},
        ).json()
    except Exception as e:
        print(f'ERROR while getting userid from username ( anilist ) \n{e}')
        return '234256'

    return response.get('data', {}).get('User', {}).get('id', '234345')


def fetch_user_data(username: str) -> UserData:
    """Fetch user from kusogaki api using username"""

    user_id = get_user_id_from_username(username)

    url = f'https://kusogaki.co/api/alwrap/statistics/{user_id}'
    params = {'wrapYear': 2024}
    headers = {'Authorization': f'Bearer {config.KUSOGAKI_TOKEN}'}

    user_data: UserData = UserData()
    data = {}

    try:
        response = requests.get(url, params=params, headers=headers)

        if response.status_code == 204:
            user_data.error = True
            user_data.error_msg = '204'
            return user_data

        response.raise_for_status()
        data = response.json()

    except requests.exceptions.HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
        user_data.error = True
        user_data.error_msg = f'HTTP error occurred: {http_err}'
        return user_data

    except Exception as err:
        print(f'Error occurred: {err}')
        user_data.error = True
        user_data.error_msg = f'Error occurred: {err}'
        return user_data

    user_data.name = data['Username']
    user_data.anime_count = data['AnimeCompleted']
    user_data.anime_eps = data['EpisodesWatched']
    user_data.anime_mean_score = data['AnimeMeanScore']

    user_data.manga_count = data['MangaCompleted']
    user_data.manga_chaps = data['ChaptersRead']
    user_data.manga_mean_score = data['MangaMeanScore']

    return user_data
