from datetime import datetime
from enum import Enum

from discord import Embed

from config import ERROR_COLOR, INFORMATION_COLOR, NORMAL_COLOR, WARNING_COLOR


class EmbedType(Enum):
    NORMAL = (0,)
    INFORMATION = (1,)
    WARNING = (2,)
    ERROR = 3


async def get_embed(
    type: EmbedType, title: str, description: str, thumbnail: bool = False
):
    embd = Embed(title=title, description=description, timestamp=datetime.now())

    if type is EmbedType.NORMAL:
        embd.color = NORMAL_COLOR
    elif type is EmbedType.INFORMATION:
        embd.color = INFORMATION_COLOR
    elif type is EmbedType.WARNING:
        embd.color = WARNING_COLOR
    elif type is EmbedType.ERROR:
        embd.color = ERROR_COLOR

    return embd
