import os
import re
from io import BytesIO
from pathlib import Path

import aiohttp
import requests
from PIL import Image, ImageFilter

ANILIST_API = 'https://graphql.anilist.co'

ANIME_POSITIONS = [(412, 305), (518, 340), (597, 340), (676, 340), (755, 340)]
MANGA_POSITIONS = [(789, 506), (895, 541), (974, 541), (1053, 541), (1132, 541)]
MEDIA_FIRST_SIZE = (97, 125)
MEDIA_SIZE = (70, 90)
IMAGES_DIR = Path('static')


def blur_image(image, radius=15):
    return image.filter(ImageFilter.GaussianBlur(radius))


async def apply_mask(image, mask, size):
    mask = mask.resize(size)
    image = image.resize(size)
    image.putalpha(mask.split()[3])
    return image


def parse_media_id(source: str) -> int | None:
    """Extract media ID"""
    if source.isdigit():
        return int(source)
    match = re.search(r'anilist\.co/(?:anime|manga)/(\d+)', source)
    return int(match.group(1)) if match else None


async def get_cover_urls(media_ids: list[int]) -> dict[int, dict]:
    """Fetch covers"""
    if not media_ids:
        return {}

    query = """
    query ($ids: [Int]) {
        Page {
            media(id_in: $ids) {
                id
                isAdult
                coverImage { extraLarge }
            }
        }
    }
    """
    async with aiohttp.ClientSession() as session:
        async with session.post(
            ANILIST_API,
            json={'query': query, 'variables': {'ids': media_ids}},
        ) as resp:
            data = await resp.json()
            return {
                m['id']: {
                    'cover': m['coverImage']['extraLarge'],
                    'isAdult': m['isAdult'],
                }
                for m in data['data']['Page']['media']
            }


async def load_image(source):
    if not source.startswith('http'):
        return None
    async with aiohttp.ClientSession() as session:
        async with session.get(source) as response_raw:
            image_raw = await response_raw.read()
            image_binary = BytesIO(image_raw)
            return Image.open(image_binary).convert('RGBA')


async def replace_media(user_id, anime_images=None, manga_images=None):
    media_mask = Image.open(IMAGES_DIR / 'media.png').convert('RGBA')
    large_media_mask = Image.open(IMAGES_DIR / 'large_media.png').convert('RGBA')

    url = f'https://kusogaki.co/images/wraps/{user_id}.png'
    img = await load_image(url)

    all_sources = list(anime_images or []) + list(manga_images or [])
    media_ids = []
    for source in all_sources:
        if source:
            media_id = parse_media_id(source)
            if media_id:
                media_ids.append(media_id)
    cover_urls = await get_cover_urls(media_ids)

    for images, positions in [
        (anime_images, ANIME_POSITIONS),
        (manga_images, MANGA_POSITIONS),
    ]:
        if not images:
            continue
        for i, source in enumerate(images):
            if not source or i >= len(positions):
                continue
            media_id = parse_media_id(source)
            media_info = cover_urls.get(media_id) if media_id else None
            if media_info:
                image_url = media_info['cover']
                is_adult = media_info['isAdult']
            else:
                image_url = source
                is_adult = False
            if not image_url:
                continue
            mask = large_media_mask if i == 0 else media_mask
            size = MEDIA_FIRST_SIZE if i == 0 else MEDIA_SIZE
            image = await load_image(image_url)
            if not image:
                continue
            if is_adult:
                image = blur_image(image)
            media = await apply_mask(image, mask, size)
            img.paste(media, positions[i], media)

    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    url = f'https://kusogaki.co/api/alwrap/apply/{user_id}'
    auth_token = os.getenv('KUSOGAKI_TOKEN')
    headers = {'Authorization': f'Bearer {auth_token}'}
    files = {'image': ('wrap.png', buffer, 'image/png')}

    response = requests.post(
        url,
        params={'wrapYear': 2025, 'updateStatus': False},
        headers=headers,
        files=files,
    )

    return response.ok
