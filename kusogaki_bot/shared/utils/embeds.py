from datetime import datetime
from enum import Enum
from typing import Optional

from discord import Embed, File


class EmbedColor(int, Enum):
    NORMAL = 0x6A1B9A
    INFORMATION = 0x546E7A
    WARNING = 0xE67E22
    ERROR = 0xE74C3C


class EmbedType(Enum):
    NORMAL = EmbedColor.NORMAL
    INFORMATION = EmbedColor.INFORMATION
    WARNING = EmbedColor.WARNING
    ERROR = EmbedColor.ERROR


async def get_embed(
    type: EmbedType, title: str, description: str, thumbnail_path: Optional[str] = None
) -> Embed:
    """
    Create a Discord embed with specified type, title, and description.

    Args:
        type (EmbedType): The type of embed which determines its color
        title (str): The embed title
        description (str): The embed description
        thumbnail_path (Optional[str]): Path to thumbnail image. If None, uses default image.

    Returns:
        Embed: A configured Discord embed
    """
    embed = Embed(
        title=title,
        description=description,
        color=type.value.value,
        timestamp=datetime.now(),
    )

    if thumbnail_path:
        file = File(thumbnail_path, filename=thumbnail_path.split('/')[-1])
        embed.set_thumbnail(url=f'attachment://{thumbnail_path.split("/")[-1]}')
    else:
        file = File('static/fern-pout.png', filename='fern-pout.png')
        embed.set_thumbnail(url='attachment://fern-pout.png')

    return embed, file
