import os
from io import BytesIO
from pathlib import Path

import aiohttp
from PIL import Image

ANIME_POSITIONS = [(412, 305), (518, 340), (597, 340), (676, 340), (755, 340)]
MANGA_POSITIONS = [(789, 506), (895, 541), (974, 541), (1053, 541), (1132, 541)]
MEDIA_FIRST_SIZE = (97, 125)
MEDIA_SIZE = (70, 90)
IMAGES_DIR = Path(__file__).parent / 'Images'


async def apply_mask(image, mask, size):
    mask = mask.resize(size)
    image = image.resize(size)
    image.putalpha(mask.split()[3])
    return image


async def load_image(source):
    if source.startswith('http'):
        async with aiohttp.ClientSession() as session:
            async with session.get(source) as response_raw:
                image_raw = await response_raw.read()
                image_binary = BytesIO(image_raw)
                return Image.open(image_binary).convert('RGBA')
    return Image.open(source).convert('RGBA')


async def replace_media(user_id, anime_images=None, manga_images=None):
    media_mask = Image.open(IMAGES_DIR / 'media.png').convert('RGBA')
    large_media_mask = Image.open(IMAGES_DIR / 'large_media.png').convert('RGBA')

    url = f'https://kusogaki.co/images/wraps/{user_id}.png'
    img = await load_image(url)

    for images, positions in [
        (anime_images, ANIME_POSITIONS),
        (manga_images, MANGA_POSITIONS),
    ]:
        if not images:
            continue
        for i, source in enumerate(images):
            if source is None or i >= len(positions):
                continue
            mask = large_media_mask if i == 0 else media_mask
            size = MEDIA_FIRST_SIZE if i == 0 else MEDIA_SIZE
            pastable_image = await load_image(source)
            media = await apply_mask(pastable_image, mask, size)
            img.paste(media, positions[i], media)

    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    url = f'https://kusogaki.co/api/alwrap/apply/{user_id}'
    headers = {'Authorization': f'Bearer {os.getenv("AUTH_TOKEN")}'}

    async with aiohttp.ClientSession() as session:
        form_data = aiohttp.FormData()
        form_data.add_field(
            'image', value=buffer, content_type='image/png', filename='wrap.png'
        )

        async with session.post(
            url, params={'wrapYear': 2025}, headers=headers, data=form_data
        ) as response_raw:
            return response_raw.ok
