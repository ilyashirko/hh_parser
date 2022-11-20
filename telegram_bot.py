import sqlite3
from functools import partial
from textwrap import dedent

from environs import Env
from telegram import (KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove,
                      Update, InlineKeyboardMarkup, InlineKeyboardButton)
from telegram.ext import (CallbackContext, CallbackQueryHandler,
                          CommandHandler, Filters, MessageHandler, Updater)

import db_processing
import settings

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        [KeyboardButton(settings.GET_VACANCY_BUTTON)],
        [KeyboardButton(settings.COUNT_ACTIVE_VACANCIES)],
        [KeyboardButton(settings.COVERING_LETTER_BUTTON)]
    ],
    resize_keyboard=True
)


def start(update: Update, context: CallbackContext) -> None:
    context.bot.send_message(
        update.effective_chat.id,
        'Привет',
        reply_markup=MAIN_KEYBOARD
    )


def send_vacancy(db: sqlite3.Connection,
                 cursor: sqlite3.Cursor,
                 update: Update,
                 context: CallbackContext) -> None:
    vacancy = db_processing.get_active_vacancy(db, cursor)
    
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=vacancy.message(),
        reply_markup=vacancy.make_tg_inline_keyboard()
    )


def count_active_vacancy(db: sqlite3.Connection,
                         cursor: sqlite3.Cursor,
                         update: Update,
                         context: CallbackContext) -> None:
    active_vacancies_num = db_processing.count_active_vacancies(db, cursor)
    context.bot.send_message(
        update.effective_chat.id,
        f'У вас {active_vacancies_num} необработанных вакансий.'
    )


def response_vacancy(db: sqlite3.Connection,
                     cursor: sqlite3.Cursor,
                     update: Update,
                     context: CallbackContext) -> None:
    context.bot.edit_message_text(
        f'{update.callback_query.message.text}\n\nUPD:\nБыл отправлен отклик.\nВакансия в архиве',
        chat_id=update.callback_query.message.chat_id,
        message_id=update.callback_query.message.message_id,
    )
    db_processing.update_response_and_process_statuses(
        db,
        cursor,
        update.callback_query.data.split(':')[1]
    )


def archive_vacancy(db: sqlite3.Connection,
                    cursor: sqlite3.Cursor,
                    update: Update,
                    context: CallbackContext) -> None:
    context.bot.edit_message_text(
        f'{update.callback_query.message.text}\n\nUPD:\nВакансия в архиве',
        chat_id=update.callback_query.message.chat_id,
        message_id=update.callback_query.message.message_id,
    )
    db_processing.update_process_status(
        db,
        cursor,
        update.callback_query.data.split(':')[1]
    )

def send_covering_letter(update: Update, context: CallbackContext):
    with open(env.str('COVERING_LETTER_PATH'), 'r') as file:
        context.bot.send_message(
            update.effective_chat.id,
            file.read()
        )
    context.bot.send_document(
        chat_id=update.effective_chat.id,
        document=open(env.str('COVERING_LETTER_PATH'), 'rb')
    )



def run_bot(tg_bot_token: str):
    update = Updater(token=tg_bot_token, use_context=True)

    update.dispatcher.add_handler(
        CommandHandler('start', start)
    )
    update.dispatcher.add_handler(
        MessageHandler(
            Filters.text([settings.GET_VACANCY_BUTTON]),
            partial(send_vacancy, db, cursor)
        )
    )
    update.dispatcher.add_handler(
        MessageHandler(
            Filters.text([settings.COVERING_LETTER_BUTTON]),
            send_covering_letter
        )
    )
    update.dispatcher.add_handler(
        MessageHandler(
            Filters.text([settings.COUNT_ACTIVE_VACANCIES]),
            partial(count_active_vacancy, db, cursor)
        )
    )
    update.dispatcher.add_handler(
        CallbackQueryHandler(
            partial(archive_vacancy, db, cursor),
            pattern='archive_vacancy'
        )
    )
    update.dispatcher.add_handler(
        CallbackQueryHandler(
            partial(response_vacancy, db, cursor),
            pattern='response_vacancy'
        )
    )
    update.start_polling()
    update.idle()

if __name__ == '__main__':
    env = Env()
    env.read_env()

    try:
        db = sqlite3.connect(env.str('DATABASE', 'vacancies.sqlite3'), check_same_thread=False)
        cursor = db.cursor()

        run_bot(env.str('TELEGRAM_BOT_TOKEN'))
    except Exception:
        print(Exception)
    finally:
        db.close()