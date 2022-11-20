from sqlite3 import Cursor, Connection
from telegram import InlineKeyboardMarkup, InlineKeyboardButton


class Vacancy:
    def __init__(self, vacancy_info: list) -> None:
        self.id = vacancy_info[0]
        self.title = vacancy_info[1]
        self.employer = vacancy_info[2]
        self.employer_url = vacancy_info[3]
        self.salary = vacancy_info[4]
        self.address = vacancy_info[5]
        self.requirements = vacancy_info[6]
        self.responsibilities = vacancy_info[7]
        self.vacancy_url = vacancy_info[8]
        self.response_url = vacancy_info[9]
        self.created_at = vacancy_info[10]
        self.responded = vacancy_info[11]
        self.processed = vacancy_info[12]
    
    def message(self):
        message = self.title
        if self.salary:
            message += f'\n{self.salary}'
        if self.employer:
            message += f'\nРаботодатель: {self.employer}'
        if self.address:
            message += f'\n{self.address}'
        if self.requirements:
            message += f'\n\nОжидания:\n{self.requirements}'
        if self.responsibilities:
            message += f'\n\nЧем предстоит заниматься:\n{self.responsibilities}'
        message += f'\n\n{self.created_at}'
        return message

    def make_tg_inline_keyboard(self):
        buttons = list()
        if self.vacancy_url:
            buttons.append([
                InlineKeyboardButton(
                    text='подробнее о вакансии',
                    url=self.vacancy_url
                )
            ])
        if self.vacancy_url:
            buttons.append([
                InlineKeyboardButton(
                    text='подробнее о работодателе',
                    url=self.employer_url
                )
            ])
        if self.vacancy_url:
            buttons.append([
                InlineKeyboardButton(
                    text='откликнуться',
                    url=self.response_url
                )
            ])
        buttons.append([
            InlineKeyboardButton(
                text='отклик отправлен',
                callback_data=f'response_vacancy:{self.id}'
            )
        ])
        if self.vacancy_url:
            buttons.append([
                InlineKeyboardButton(
                    text='в архив',
                    callback_data=f'archive_vacancy:{self.id}'
                )
            ])
        return InlineKeyboardMarkup(buttons)

def add_vacancy(db: Connection, cursor: Cursor, vacancy_info: list):
    assert len(vacancy_info) == 13
    cursor.execute(
        "INSERT INTO vacancies VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
        vacancy_info
    )
    db.commit()


def get_active_vacancy(db: Connection, cursor: Cursor) -> Vacancy:
    vacancy_info = cursor.execute(
        "SELECT * FROM vacancies WHERE processed = False LIMIT 1"
    ).fetchone()
    return Vacancy(vacancy_info)


def count_active_vacancies(db: Connection, cursor: Cursor):
    return cursor.execute(
        "SELECT COUNT(*) FROM vacancies WHERE processed = False"
    ).fetchone()[0]


def update_response_and_process_statuses(db: Connection,
                           cursor: Cursor,
                           vacancy_id: int) -> None:
    cursor.execute(
        """UPDATE vacancies SET responded = 1, processed = 1 WHERE id = ?""",
        (vacancy_id,)
    )
    db.commit()

def update_process_status(db: Connection,
                           cursor: Cursor,
                           vacancy_id: int) -> None:
    cursor.execute(
        """UPDATE vacancies SET processed = 1 WHERE id = ?""",
        (vacancy_id,)
    )
    db.commit()