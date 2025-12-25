from os import getenv

from dotenv import load_dotenv

load_dotenv()

TOKEN = getenv('TOKEN')
STAFF_ROLE_ID = getenv('STAFF_ROLE_ID')
AWAIZ_USER_ID = getenv('AWAIZ_USER_ID')
KUSOGAKI_TOKEN = getenv('KUSOGAKI_TOKEN')

ANILIST_BASE = 'https://graphql.anilist.co'
