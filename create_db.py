import sqlite3

from environs import Env


def create_tables(fs, cursor):
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS vacancies(
            id INTEGER,
            title TEXT,
            employer TEXT,
            employer_url TEXT,
            salary TEXT,
            address TEXT,
            requirements TEXT,
            responsibilities TEXT,
            vacancy_url TEXT,
            response_url TEXT,
            created_at INTEGER,
            responded INTEGER,
            processed INTEGER
        );
        """
    )
    
    fs.commit()


if __name__ == '__main__':
    env = Env()
    env.read_env()

    db = sqlite3.connect(env.str('DATABASE', 'vacancies.sqlite3'))
    cursor = db.cursor()

    create_tables(db, cursor)
