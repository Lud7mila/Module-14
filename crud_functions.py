import sqlite3
from venv import logger
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


products = [
        (1, "Крем-шоколад", "Урбеч кокосовый", 1200),
        (2, "Амарант и мёд", "Урбеч со скваленом", 1400),
        (3, "Чёрный тмин", "Урбеч из тмина", 1600),
        (4, "Кокос и миндаль", "Урбеч без сахара", 1300)
    ]

def initiate_db():
    # Устанавливаем соединение с базой данных
    connection = sqlite3.connect('Products.db')
    cursor = connection.cursor()

    # Создаём таблицу
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Products(
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    price INTEGER NOT NULL
    )
    ''')

    try:
        cursor.executemany("INSERT OR IGNORE INTO Products VALUES(?, ?, ?, ?)", products)
    except:
        logger.warning("Не удалось добавить данные в БД", exc_info=True)

    connection.commit()
    connection.close()


def get_all_products():
    result = None
    try:
        # Устанавливаем соединение с базой данных
        connection = sqlite3.connect('Products.db')
        # установим возвращение ответа на запрос в виде словаря
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM Products")
        result = cursor.fetchall()

        connection.close()
    except:
        logger.error('No data available', exc_info=True)

    return result


if __name__ == '__main__':
    initiate_db()
    rows = get_all_products()
    if rows:
        [print(row['id'], row['title'], row['description'], row['price']) for row in rows]

