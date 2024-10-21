from os import getenv

from dotenv import load_dotenv

NORMAL_COLOR = 0x2B2D31
INFORMATION_COLOR = 0x546e7a
WARNING_COLOR = 0xe67e22
ERROR_COLOR = 0xe74c3c

load_dotenv()

TOKEN = getenv('TOKEN')
LOG_CHANNEL_ID = getenv('LOG_CHANNEL_ID')
