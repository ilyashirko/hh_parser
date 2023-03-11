import os
import sqlite3
import sys

from time import sleep

import requests
from environs import Env
from telegram import Bot
from tqdm import tqdm

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

# import settings
# from database import db_processing







HH_API_URL = 'https://api.hh.ru/vacancies'

UPDATE_DELAY = 60*10

def clean_text(text: str) -> str:
    trash = [
        '<highlighttext>',
        '</highlighttext>',
    ]
    for item in trash:
        text = ''.join(text.split(item))
    return text


def convert_salary(salary: dict) -> str:
    salary_from = f'от {salary["from"]} ' if salary["from"] else ''
    salary_to = f'до {salary["to"]} ' if salary["to"] else ''
    return f'{salary_from}{salary_to}({salary["currency"]})'


def run_hh_parser(hh_headers: dict,
                  db: sqlite3.Connection,
                  cursor: sqlite3.Cursor,
                  bot: Bot) -> None:
    response = requests.get(
        HH_API_URL,
        headers=hh_headers,
        params=settings.PYTHON_DEV_HH_PARAMS
    )
    response.raise_for_status()
    vacancies = response.json()['items']
    for vacancy in tqdm(vacancies, desc='processing vacancies'):
        print(vacancy['name'])
        if vacancy['type']['id'] != 'open':
            print('47 CONTINUE')
            continue

        address = vacancy['address']
        if address:
            address = f"{address['city']}, {address['street']}, {address['building']}"

        salary = vacancy['salary']
        if salary:
            salary = convert_salary(salary)

        requirements = vacancy['snippet']['requirement']
        if requirements:
            requirements = clean_text(requirements)

        responsibilities = vacancy['snippet']['responsibility']
        if responsibilities:
            responsibilities = clean_text(responsibilities)

        parsed_vacancy = {
            'id': vacancy['id'],
            'title': vacancy['name'],
            'employer': vacancy['employer']['name'],
            'employer_url': vacancy['employer']['url'],
            'salary': salary,
            'address': address,
            'requirements': requirements,
            'responsibilities': responsibilities,
            'vacancy_url': vacancy['alternate_url'],
            'response_url': vacancy['apply_alternate_url'],
            'created_at': vacancy['created_at'],
            'responded': False,
            'processed': False
        }
        print('PARSED')
        check_vacancy = cursor.execute(
            "SELECT id FROM vacancies WHERE id = ?",
            (parsed_vacancy['id'],)
        ).fetchone()
        print('CHECKED')
        if not check_vacancy:
            print('checked')
            vacancy_object = db_processing.Vacancy(list(parsed_vacancy.values()))
            print('created')
            for telegram_id in env.list('USERS'):
                print(telegram_id)
                bot.send_message(
                    telegram_id,
                    text=vacancy_object.message(),
                    reply_markup=vacancy_object.make_tg_inline_keyboard()
                )
            print('sent')
            db_processing.add_vacancy(
                db,
                cursor,
                list(parsed_vacancy.values()),
            )
            print('inputed')


if __name__ == '__main__':
    env = Env()
    env.read_env()

    db = sqlite3.connect(os.path.join(settings.DB_ROOT_FOLDER, env.str('DATABASE', 'vacancies.sqlite3')))
    cursor = db.cursor()

    bot = Bot(env.str("TELEGRAM_BOT_TOKEN"))

    hh_headers = {'User-Agent': env.str('USER_AGENT')}
    while True:
        run_hh_parser(hh_headers, db, cursor, bot)
        sleep(UPDATE_DELAY)