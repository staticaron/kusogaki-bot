from os import environ, getenv

from dotenv import load_dotenv

if 'RAILWAY_ENVIRONMENT' not in environ:
    load_dotenv()

TOKEN = getenv('TOKEN')
STAFF_ROLE_ID = int(getenv('STAFF_ROLE_ID'))
AWAIZ_USER_ID = getenv('AWAIZ_USER_ID')
