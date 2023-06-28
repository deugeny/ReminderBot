from datetime import datetime
from typing import Never, cast, Tuple

from telegram import Update, Message, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, Job, ExtBot, ConversationHandler, CommandHandler, CallbackQueryHandler, \
    InvalidCallbackData, MessageHandler, filters

import message_receiver
from get_jobs import get_jobs
from config import CANCEL_REMIND, BACK, logger, START_DIALOG, SELECTING_ACTION, END, ADD_REMIND, SHOW_MY_REMIND, \
    CANCEL_ALL_MY_REMIND, CONFIRM_CANCELLATION, UNCONFIRM_CANCELLATION, PARSE_REMIND, STOPPING, RECEIVER_ID
from parsing import find_scheduling_datetime
from start_handler import start, stop
from validation import Validation, ValidationKey


async def adding_remind(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    buttons = [[InlineKeyboardButton(text="Назад", callback_data=str(BACK))]]
    keyboard = InlineKeyboardMarkup(buttons)
    text = ("<b>Введите текст напоминания.</b>"
            "\n\nДля указания даты Вы можете использовать как точное указание даты и времени так и текстовые "
            "обозначения сегодня, завтра, через час"
            "\nНапример:<i>Завтра в 18:00 MSK необходимо запустить выполнение задачи по ТТ2233445566</i>")
    try:
        await context.bot.send_message(text=text, chat_id=update.effective_chat.id, reply_markup=keyboard)
    except BaseException as e:
        logger.exception(e)

    return str(PARSE_REMIND)

async def send_message(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    text = job.data['text']
    try:
        await context.bot.send_message(job.chat_id, text=f"{text}")
    except BaseException as e:
        logger.exception(e)

async def parse_remind(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    text = update.message.text
    date = find_scheduling_datetime(text)
    validation_result = (
        Validation
        .start()
        .error(
            "дата/время показа напоминания не распознаны или отсутствуют в тексте.",
            ValidationKey.INVALID_DATA,
            date is None)
        .build())

    if validation_result.has_validation_key(ValidationKey.INVALID_DATA):
        await update.message.reply_text(text=validation_result.message)
        return await adding_remind(update, context)

    chat_id = message_receiver.try_get_receiver_id(context)
    try:
        data = {
            "from_chat_id": update.effective_chat.id,
            "from_user_id": update.effective_user.id,
            "text" : text,
        }
        job = context.job_queue.run_once(send_message, when=date, name=str(update.message.id),
                                         chat_id=chat_id,
                                         user_id=update.message.from_user.id, data=data)
        await print_job(job, update.effective_chat.id, context.bot)
    except Exception as e:
        await update.message.reply_text(text='Ошибка добавления напоминания')
        logger.exception(e)
    return str(SELECTING_ACTION)
async def show_my_remind(update: Update, context: ContextTypes.DEFAULT_TYPE) -> [None|str]:
    jobs = get_jobs(update.effective_user.id, context.job_queue.jobs())
    if len(jobs) == 0:
        text = "Нет активных напоминаний!!!"
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
        return None

    for job in jobs:
        await print_job(job, update.effective_chat.id, context.bot)

    return None


async def print_job(printing_job: "Job", chat_id: int, bot: ExtBot) -> Message:
    def datetime_repr(date: datetime | None) -> str:
        return date.strftime('%H:%M:%S %Z %d-%m-%Y') if date else 'Не указано'

    text = (
        f'⏰ Напоминание: <b>#{printing_job.job.name}</b>'
        f'\nЗапуск в: <b>{datetime_repr(printing_job.job.next_run_time)}</b>'
        '\n---------------------------------------------------------------------------'
        f'\n<pre>{printing_job.data["text"]}</pre>')
    buttons = [[InlineKeyboardButton(text="Отменить", callback_data=(CANCEL_REMIND, printing_job.name))]]
    keyboard = InlineKeyboardMarkup(buttons)
    return await bot.send_message(chat_id=chat_id,
                                  parse_mode=ParseMode.HTML,
                                  text=text,
                                  reply_markup=keyboard)


async def cancel_all_my_remind(update: Update, context: ContextTypes.DEFAULT_TYPE) -> [str|None]:
    jobs = get_jobs(update.effective_user.id, context.job_queue.jobs())
    jobs_count = len(jobs)
    if jobs_count == 0:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Нет напоминаний для отмены")
        return None

    buttons = [[InlineKeyboardButton(text="Да", callback_data=CONFIRM_CANCELLATION), InlineKeyboardButton(text="Нет", callback_data=UNCONFIRM_CANCELLATION)]]
    keyboard = InlineKeyboardMarkup(buttons)
    await context.bot.send_message(chat_id=update.effective_chat.id, reply_markup=keyboard, text = f'Отменить все Ваши напоминания ({jobs_count})?')
    return str(CANCEL_ALL_MY_REMIND)

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    jobs = get_jobs(update.effective_user.id, context.job_queue.jobs())
    jobs_count = len(jobs)
    if jobs_count > 0:
        for job in jobs:
            job.job.remove()
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Напоминания отменены!!!")
    return await start(update, context)

async def unconfirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    return await start(update, context)

async def handle_invalid_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Never:
    await update.callback_query.answer()
    await update.effective_message.edit_text(
        "Ошибка обработки события от кнопки😕. Пожалуйста отправьте команду /start для новой интеракции."
    )


async def cancel_job(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _, job_name = update.callback_query.data
    try:
        jobs = context.job_queue.get_jobs_by_name(name=job_name)
        for job in jobs:
            job.schedule_removal()
        text = update.callback_query.message.text
        buttons = [[InlineKeyboardButton(text="«Назад", callback_data=str(BACK))]]
        await update.callback_query.message.edit_text(text=f"<s>{text}</s>", reply_markup=None, parse_mode=ParseMode.HTML)

    except Exception as e:
        logger.exception(f"Exception raised in {cancel_job.__name__}. exception: {str(e)}")
    return None#await self.start(update, context)

def is_cancel_data(data: object) -> bool:
    command = ''
    if isinstance(data, tuple):
        command, _ = cast(Tuple[chr, str], data)
    return command == CANCEL_REMIND
def create_conversation_handler() -> ConversationHandler:

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            START_DIALOG: [CallbackQueryHandler(start, pattern="^" + str(END) + "$")],
            SELECTING_ACTION: [
                CallbackQueryHandler(stop, pattern="^" + str(END) + "$"),
                CallbackQueryHandler(adding_remind, pattern="^" + str(ADD_REMIND) + "$"),
                CallbackQueryHandler(show_my_remind, pattern="^" + str(SHOW_MY_REMIND) + "$"),
                CallbackQueryHandler(cancel_all_my_remind, pattern="^" + str(CANCEL_ALL_MY_REMIND) + "$"),
                CallbackQueryHandler(handle_invalid_button, pattern=InvalidCallbackData)
            ],
            CANCEL_ALL_MY_REMIND:[
                CallbackQueryHandler(confirm, pattern="^" + str(CONFIRM_CANCELLATION) + "$"),
                CallbackQueryHandler(unconfirm, pattern="^" + str(UNCONFIRM_CANCELLATION) + "$")
            ],
            PARSE_REMIND: [
                MessageHandler(filters.TEXT & (~filters.COMMAND), parse_remind),
                CallbackQueryHandler(start, pattern="^" + str(BACK) + "$"),
            ],
            STOPPING: [CommandHandler("start", start)],
        },
        fallbacks=[
            CommandHandler("start", start),
            CommandHandler("stop", stop)],
    )
    return conv_handler
