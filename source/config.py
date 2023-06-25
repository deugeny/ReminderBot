import os
import logging
from datetime import timedelta
from pytz import timezone
from sqlalchemy import create_engine
from telegram.ext import ConversationHandler
from sqlalchemy_utils.functions import database_exists, create_database

# идентификатор бота
API_TOKEN = os.getenv('REMINDER_BOT_API_TOKEN', default='5957265855:AAGjxqDh-XqfUVFfIY6WdtjIt2OWhdFwQuA')
DEFAULT_RECEIVER_CHAT_ID = os.getenv('RECEIVER_CHAT_ID', default=0)

# путь к базе данных
DATABASE_CONNECTION_STRING = os.getenv('REMINDER_BOT_CONNECTION_STRING', default='sqlite:///jobs.db')
DEFAULT_TZNAME: str = 'Europe/Moscow'
DEFAULT_TZ: timezone = timezone(DEFAULT_TZNAME)

DATE_SEARCH_SETTINGS = {'TIMEZONE': DEFAULT_TZNAME, 'RETURN_AS_TIMEZONE_AWARE': True, 'PREFER_DATES_FROM': 'future'}
DATE_SEARCH_LANGUAGES = ['ru', 'en']

BOT_ADMINS= (int(admin_id) for admin_id in os.getenv('REMINDER_BOT_ADMINS', default='156302877').split(','))

MINIMUM_SCHEDULING_PERIOD = timedelta(seconds=10)
DEVELOPER_CHAT_ID = '5235429783:AAFT8GrhRazJalixcmwr2TNZOT-I0LZKICg'

(
    START_DIALOG,
    SELECTING_ACTION,
    ADD_REMIND,
    SHOW_MY_REMIND,
    CANCEL_REMIND,
    CANCEL_ALL_MY_REMIND,
    CONFIRM_CANCELLATION,
    UNCONFIRM_CANCELLATION,
    PARSE_REMIND,
    STOPPING,
    BACK
) = map(chr, range(0, 11))
END = ConversationHandler.END

RECEIVER_ID = "RECEIVER_ID"

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.ERROR)
logger = logging.getLogger(__name__)

engine = create_engine(DATABASE_CONNECTION_STRING, echo=True, query_cache_size=1200)
if not database_exists(engine.url):
    create_database(engine.url)