from discord import Embed

from enum import Enum
from datetime import datetime

from config import NORMAL_COLOR, INFORMATION_COLOR, WARNING_COLOR, ERROR_COLOR

class EmbedType(Enum):
    NORMAL = 0,
    INFORMATION = 1,
    WARNING = 2, 
    ERROR = 3

async def get_embed(_type: EmbedType, _title: str, _description: str, _thumbnail: bool):
    
    embd = Embed(title=_title, description=_description, timestamp=datetime.now())
    
    if _type is EmbedType.NORMAL:
        embd.color = NORMAL_COLOR
    elif _type is EmbedType.INFORMATION:
        embd.color = INFORMATION_COLOR
    elif _type is EmbedType.WARNING:
        embd.color = WARNING_COLOR
    elif _type is EmbedType.ERROR:
        embd.color = ERROR_COLOR
        
    return embd