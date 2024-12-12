import sqlite3
import logging

#logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger1 = logging.getLogger(__name__)


products = [
        (1, "Крем-шоколад", "Урбеч кокосовый", 1200),
        (2, "Амарант и мёд", "Урбеч со скваленом", 1400),
        (3, "Чёрный тмин", "Урбеч из тмина", 1600),
        (4, "Кокос и миндаль", "Урбеч без сахара", 1300)
    ]

# Устанавливаем соединение с базой данных Products
connectionProd = sqlite3.connect('Products.db')
#connectionProd.row_factory = sqlite3.Row
cursorProd = connectionProd.cursor()

# Устанавливаем соединение с базой данных Users
connectionUsers = sqlite3.connect('Users.db')
#connectionUsers.row_factory = sqlite3.Row
cursorUsers = connectionUsers.cursor()

def initiate_db():
    # Создаём таблицу Products
    cursorProd.execute('''
    CREATE TABLE IF NOT EXISTS Products(
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    price INTEGER NOT NULL
    )
    ''')
    # добавляем данные в БД Products, если их ещё нет в БД
    cursorProd.executemany("INSERT OR IGNORE INTO Products VALUES(?, ?, ?, ?)", products)
    connectionProd.commit()

    # Создаём таблицу Users
    cursorUsers.execute('''
        CREATE TABLE IF NOT EXISTS Users(
        id INTEGER PRIMARY KEY,
        username TEXT NOT NULL,
        email TEXT NOT NULL,
        age INTEGER NOT NULL,
        balance INTEGER NOT NULL
        )
        ''')
    connectionUsers.commit()


def get_all_products():
    prod_dict = []
    try:
        cursorProd.execute("SELECT * FROM Products")
        prod = cursorProd.fetchall()
        connectionProd.commit()
        for product in prod:
            prod_dict.append({"id": product[0], "title": product[1], "description": product[2], "price": product[3]})
    except:
        logger1.error('No data available', exc_info=True)
        prod_dict = None
    return prod_dict


def count_users():
    users_count = (cursorUsers.execute("SELECT COUNT(*) FROM Users").fetchone())[0]
    connectionUsers.commit()
    return users_count

def is_included(username):
    count_users = (cursorUsers.execute(f"SELECT COUNT(*) FROM Users WHERE username = \'{username}\'").fetchone())[0]
    connectionUsers.commit()
    if count_users > 0:
        return True
    return False

def add_user(username, email, age):
    if is_included(username):
        return False # Такой пользователь \'{username}\' уже есть в БД
    else:
        cursorUsers.execute(f'INSERT INTO Users VALUES({count_users() + 1}, \'{username}\', \'{email}\', {age}, 1000)')
        connectionUsers.commit()
        return True


if __name__ == '__main__':
    initiate_db()
    rows = get_all_products()
    if rows:
        [print(row['id'], row['title'], row['description'], row['price']) for row in rows]

    print(add_user("Петя", "ff3@a.ru", 25))

    connectionUsers.commit()
    connectionUsers.close()

    connectionProd.commit()
    connectionProd.close()
