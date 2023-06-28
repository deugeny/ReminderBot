from typing import Never

from telegram import KeyboardButtonRequestChat, KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

import config
from config import RECEIVER_ID


def try_get_receiver_id(context:ContextTypes.DEFAULT_TYPE) -> [int|None]:
    if config.ENABLED_RECEIVER_SELECTION:
        return context.user_data.get(RECEIVER_ID)
    else:
        return config.DEFAULT_RECEIVER_CHAT_ID

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> [int, None]:
    receiver_id = None
    if update.message.chat_shared is not None and update.message.chat_shared.request_id == update.effective_chat.id:
        receiver_id = update.message.chat_shared.chat_id

    if update.message.user_shared is not None and update.message.user_shared.request_id == update.effective_chat.id:
        receiver_id = update.message.user_shared.user_id
    if receiver_id is None:
        return None
    __set_receiver_id(context, receiver_id)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Выбран получатель с id:{receiver_id}")
    return None

def __set_receiver_id( context: ContextTypes.DEFAULT_TYPE, receiver_id:[int | None]) -> Never:
    context.user_data[RECEIVER_ID] = receiver_id


def __get_receiver_text(receiver_id: int) -> str:
    receiver_text = (
        f"\nОтправка сообщений осуществляется в чат:{receiver_id}." if receiver_id is not None else "\n<b>Получатель не выбран</b>!!!")
    return f"{receiver_text}"


async def send_select_receiver_message(update: Update, context:ContextTypes.DEFAULT_TYPE) -> Never:
    if not config.ENABLED_RECEIVER_SELECTION:
        return

    select_receiver_markup = await __create_select_receiver_markup(update)
    receiver_id = try_get_receiver_id(context)
    receiver_message_text = __get_receiver_text(receiver_id)
    try:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       reply_markup=select_receiver_markup,
                                       parse_mode=ParseMode.HTML,
                                       text=receiver_message_text)
    except BaseException as e:
        config.logger.exception(e)
async def __create_select_receiver_markup(update: Update) -> ReplyKeyboardMarkup:
    request_chat = KeyboardButtonRequestChat(request_id=update.effective_chat.id, chat_is_channel=False,
                                             chat_is_forum=False)
    button = KeyboardButton(text="Выбрать получателя", request_chat=request_chat)
    markup = ReplyKeyboardMarkup(keyboard=[[button]], one_time_keyboard=True)
    return markup