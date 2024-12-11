import sqlite3

# Устанавливаем соединение с базой данных
connection = sqlite3.connect('not_telegram.db')
cursor = connection.cursor()

# Удаление данных с id = 6
cursor.execute('DELETE FROM Users WHERE id = 6')

# Посчёт суммы всех балансов
cursor.execute('SELECT SUM(balance) FROM Users')
all_balances = cursor.fetchone()[0]

# подсчёт общего количества записей в БД
cursor.execute('SELECT COUNT(*) FROM Users')
total_users = cursor.fetchone()[0]

# средний баланс всех пользователей
print(all_balances/total_users)


connection.commit()
connection.close()