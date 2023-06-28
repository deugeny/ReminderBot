from typing import Never

from telegram import __version__ as TG_VER, BotCommand, Update
from telegram.constants import ParseMode
from telegram.ext import Defaults, Application, MessageHandler, filters, \
    CallbackQueryHandler

import message_receiver
from commands import initialize_commands_menu
from config import DEFAULT_TZ, API_TOKEN, DATABASE_CONNECTION_STRING, engine
from conversation_handlers import cancel_job, create_conversation_handler, is_cancel_data
from error_handler import error_handler
from job_store import PTBSQLAlchemyJobStoreV20

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(f"Данный бот не совместим с Вашей версией  PTB {TG_VER}.")


def main() -> Never:
    commands = [
        BotCommand("start", "Запустить диалог взаимодействия с ботом"),
        BotCommand("stop", "Завершить диалог взаимодействия с ботом")
    ]

    application = create_application()
    initialize_commands_menu(application.bot, commands)
    initialize_handlers(application)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


def initialize_handlers(application: Application) -> Never:
    application.add_handler(create_conversation_handler())
    application.add_error_handler(error_handler)
    application.add_handler(MessageHandler(filters.ALL, message_receiver.message_handler))
    application.add_handler(CallbackQueryHandler(cancel_job, pattern=is_cancel_data))


def create_application():
    defaults = Defaults(parse_mode=ParseMode.HTML, tzinfo=DEFAULT_TZ)
    application = (
        Application.builder()
        .concurrent_updates(False)
        .arbitrary_callback_data(True)
        .defaults(defaults)
        .token(API_TOKEN)
        .build())
    job_store = PTBSQLAlchemyJobStoreV20(url=DATABASE_CONNECTION_STRING,
                                         engine=engine,
                                         application=application)
    application.job_queue.scheduler.add_jobstore(jobstore=job_store)
    return application


if __name__ == "__main__":
    main()