import asyncio
import html
import json
import traceback
from typing import Never, List, Tuple, cast

from telegram import __version__ as TG_VER, BotCommand, Update
from telegram.constants import ParseMode
from telegram.ext import Defaults, Application, ContextTypes, MessageHandler, filters, \
    CallbackQueryHandler

from config import DEFAULT_TZ, API_TOKEN, DATABASE_CONNECTION_STRING, engine, logger, DEVELOPER_CHAT_ID, RECEIVER_ID, \
    CANCEL_REMIND
from conversation_handlers import cancel_job, create_conversation_handler
from job_store import PTBSQLAlchemyJobStoreV20

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(f"Данный бот не совместим с Вашей версией  PTB {TG_VER}.")


def main() -> Never:
    application = create_application()

    commands = [
        BotCommand("start", "Запустить диалог взаимодействия с ботом"),
        BotCommand("stop", "Завершить диалог взаимодействия с ботом")
    ]
    init_bot_commands_menu(application.bot, commands)
    application.add_handler(create_conversation_handler())
    application.add_error_handler(error_handler)
    application.add_handler(MessageHandler(filters.ALL, message_handler))

    application.add_handler(CallbackQueryHandler(cancel_job, pattern=is_cancel_data))
    application.run_polling(allowed_updates=Update.ALL_TYPES)

def is_cancel_data(data: object) -> bool:
    command = ''
    if isinstance(data, tuple):
        command, _ = cast(Tuple[chr, str], data)
    return command == CANCEL_REMIND


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> [int, None]:
    receiver_id = None
    if update.message.chat_shared is not None and update.message.chat_shared.request_id == update.effective_chat.id:
        receiver_id = update.message.chat_shared.chat_id

    if update.message.user_shared is not None and update.message.user_shared.request_id == update.effective_chat.id:
        receiver_id = update.message.user_shared.user_id
    if receiver_id is None:
        return None
    context.user_data[RECEIVER_ID] = receiver_id
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Выбран получатель с id:{receiver_id}")
    return None



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


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        f"Возникла необработанная ошибка при обработке обновления\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )

    await context.bot.send_message(chat_id=DEVELOPER_CHAT_ID, text=message, parse_mode=ParseMode.HTML)
async def set_commands(bot, commands: List[BotCommand]) -> Never:
    # commands = [BotCommand("/start", "Запуск бота")]
    await bot.set_my_commands(commands)

def init_bot_commands_menu(bot, commands):
    if len(commands) > 0:
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(set_commands(bot=bot, commands=commands))
        finally:
            pass


if __name__ == "__main__":
    main()