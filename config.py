from os import getenv

from dotenv import load_dotenv

load_dotenv()

TOKEN = getenv('TOKEN')
TEST_TOKEN = getenv('TEST_TOKEN')
STAFF_ROLE_ID = getenv('STAFF_ROLE_ID')
AWAIZ_USER_ID = getenv('AWAIZ_USER_ID')
KUSOGAKI_TOKEN = getenv('KUSOGAKI_TOKEN')

ANILIST_BASE = 'https://graphql.anilist.co'

WRAP_LOG_CHANNEL_ID = int(getenv('WRAP_LOG_CHANNEL_ID') or 0)
