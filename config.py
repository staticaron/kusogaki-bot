from os import getenv

from dotenv import load_dotenv

NORMAL_COLOR = 0x2B2D31
INFORMATION_COLOR = 0x546e7a
WARNING_COLOR = 0xe67e22
ERROR_COLOR = 0xe74c3c

NEXT_EMOTE = "<:next:995484808207683604>"
PREV_EMOTE = "<:prev:995484847139209238>"
FIRST_EMOTE = "<:first:996104181515571201>"
LAST_EMOTE = "<:last:996104225459277854>"

GTA_SEASON = "summer-2024"

load_dotenv()

TOKEN = getenv('TOKEN')
LOG_CHANNEL_ID = getenv('LOG_CHANNEL_ID')
