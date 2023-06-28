from typing import Tuple

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, Job

import config
import message_receiver
from config import ADD_REMIND, SHOW_MY_REMIND, CANCEL_ALL_MY_REMIND, END, SELECTING_ACTION


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    welcome_message_text = await _get_start_message(update, context.job_queue.jobs())
    remind_control_markup = await _create_remind_control_markup()
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   reply_markup=remind_control_markup,
                                   parse_mode=ParseMode.HTML,
                                   text=welcome_message_text)
    try:
        await message_receiver.send_select_receiver_message(update, context)
    except BaseException as e:
        config.logger.exception(e)
    return str(SELECTING_ACTION)

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    await context.bot.send_message(context, chat_id=update.effective_chat.id, text="До новых встреч", ReplyKeyboardMarkup=ReplyKeyboardRemove())
    return str(END)


async def _get_start_message(update:Update, jobs:Tuple["Job['APSJob']"]) -> str:
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    user_jobs = list(
        filter(lambda job: (job.user_id == user_id), jobs))
    jobs_count = len(user_jobs)

    text = (f"Привет, {user_name}!!!"
            "\n----------------------------------------------------"
            "\nЯ, бот  управления напоминаниями"
            "\nДля изменения получателя напоминаний нажмите на кнопку <b>Выбрать получателя</b>."
            "\nДля прекращения работы бота в любой момент наберите /stop"
            "\n----------------------------------------------------"
            f"\nАктивные задания:{jobs_count}")
    return text
async def _create_remind_control_markup() -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(text="⏰ Добавить напоминание", callback_data=str(ADD_REMIND))],
               [InlineKeyboardButton(text="🔍 Показать мои напоминания", callback_data=str(SHOW_MY_REMIND))],
               [InlineKeyboardButton(text="Отменить все мои напоминания", callback_data=str(CANCEL_ALL_MY_REMIND))]]
    return InlineKeyboardMarkup(buttons)

