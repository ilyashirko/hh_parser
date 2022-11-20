from sqlite3 import Cursor, Connection


def add_vacancy(db: Connection, cursor: Cursor, vacancy_info: list):
    cursor.execute(
        "INSERT INTO vacancies VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
        vacancy_info
    )
    db.commit()