import requests
from environs import Env
import sqlite3
from settings import PYTHON_DEV_HH_PARAMS
import db_processing
from tqdm import tqdm

HH_API_URL = 'https://api.hh.ru/vacancies'


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
                  cursor: sqlite3.Cursor) -> None:
    response = requests.get(
        HH_API_URL,
        headers=hh_headers,
        params=PYTHON_DEV_HH_PARAMS
    )
    response.raise_for_status()
    vacancies = response.json()['items']
    for vacancy in tqdm(vacancies, desc='processing vacancies'):

        if vacancy['type']['id'] != 'open':
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
            'processed': False
        }
        check_vacancy = cursor.execute(
            "SELECT id FROM vacancies WHERE id = ?",
            (parsed_vacancy['id'],)
        ).fetchone()
        if not check_vacancy:
            db_processing.add_vacancy(
                db,
                cursor,
                list(parsed_vacancy.values()),
            )


if __name__ == '__main__':
    env = Env()
    env.read_env()

    db = sqlite3.connect(env.str('DATABASE', 'vacancies.sqlite3'))
    cursor = db.cursor()

    hh_headers = {'User-Agent': env.str('USER_AGENT')}
    run_hh_parser(hh_headers, db, cursor)