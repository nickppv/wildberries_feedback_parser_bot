import sqlite3
from datetime import datetime


def write_user_on_start(message):
    '''функция добавления пользователя при запуске бота'''
    # подключаемся к БД
    conn = sqlite3.connect('db_wb.sqlite3')
    # объект "курсор" позволяет делать запросы к БД
    cursor = conn.cursor()
    cursor.execute(
        '''CREATE TABLE IF NOT EXISTS users (
            user_id INT PRIMARY KEY,
            name VARCHAR(64),
            surname VARCHAR(64),
            username VARCHAR(32),
            date VARCHAR(30))'''
            )
    # получаем данные из БД и сравниваем на дублирование записей
    cursor.execute('SELECT user_id FROM users')
    users_data = cursor.fetchall()
    users_data = [int(i[0]) for i in users_data if len(users_data) > 0]
    print(users_data)
    if message.from_user.id not in users_data:
        # получаем данные пользователя, которые передадим потом в БД кортежем
        user = (
            message.from_user.id,
            message.from_user.first_name,
            message.from_user.last_name,
            message.from_user.username,
            datetime.now().strftime("%d.%m.%Y, %H:%M")
            )
        # метод с вопросительными знаками позволяет защититься от sql-инъекций
        cursor.execute(
            '''INSERT INTO users (
                user_id, name, surname, username, date
                ) VALUES (?, ?, ?, ?, ?)''', user)
        conn.commit()
        print('добавили юзера в бд')
    cursor.close()
    conn.close()


def add_feedback(limit_to_six):
    '''функция добавления отзыва в БД'''

    conn = sqlite3.connect('db_wb.sqlite3')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS wb_feedback (
                   feedback_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                   product_name VARCHAR(255), username VARCHAR(150),
                   feedback TEXT, rating INT
                   )''')
    product_name = limit_to_six[0][1] + ' ' + limit_to_six[0][0]
    feedback_text = limit_to_six[0][3]
    print(product_name)
    if not search_same_records(product_name, feedback_text):
        for i in limit_to_six:
            data = (product_name, i[2], i[3], 0)
            print('data -', data)
            cursor.execute(
                '''INSERT INTO wb_feedback (
                    product_name, username, feedback, rating
                    ) VALUES (?, ?, ?, ?)''', data)
    else:
        print('отзыв не был добавлен, т.к. уже есть такой продукт в БД')
    conn.commit()
    cursor.close()
    conn.close()


def search_same_records(record, feedback_text):
    '''функция ищет записи-дубликаты в БД'''

    conn = sqlite3.connect('db_wb.sqlite3')
    cursor = conn.cursor()
    # такой способ форматирования строки, т.к. f-строка не работает с sqlite
    cursor.execute("SELECT product_name FROM wb_feedback WHERE product_name = '%s' and feedback = '%s'" % (record, feedback_text))
    res = cursor.fetchall()
    cursor.close()
    conn.close()
    return res


def vote_for_feedback(elem):
    '''функция обновляет рейтинг, увеличивая его на единицу'''

    # условие создано для того чтобы этой функцией можно было пользоваться:
    # 1 - для голосования после поиска на сайте; 2 - для голосования из БД
    if len(elem) == 5:
        product_name = elem[1] + ' ' + elem[0]
        feedback_text = elem[3]
    else:
        product_name = elem[0]
        feedback_text = elem[2]
    conn = sqlite3.connect('db_wb.sqlite3')
    cursor = conn.cursor()
    cursor.execute("UPDATE wb_feedback SET rating=rating+1 WHERE product_name = '%s' and feedback = '%s'" % (product_name, feedback_text))
    conn.commit()
    cursor.close()
    conn.close()
    print('обновили рейтинг отзыва с продуктом и текстом: ', product_name, feedback_text, sep='\n')


def get_the_most_terrible():
    '''получить подборку из десяти самых отвратительных отзывов'''

    conn = sqlite3.connect('db_wb.sqlite3')
    cursor = conn.cursor()
    res = cursor.execute('SELECT product_name, username, feedback, rating FROM wb_feedback ORDER BY rating DESC LIMIT 6')
    result = [i for i in res]
    conn.commit()
    cursor.close()
    conn.close()
    return result


def get_count_db_records():
    '''получаем общее количество записей в БД'''

    conn = sqlite3.connect('db_wb.sqlite3')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(feedback_id) as cnt FROM wb_feedback')
    result = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return result


def get_random_records(id_values):
    '''получаем случайные шесть записей из БД'''

    conn = sqlite3.connect('db_wb.sqlite3')
    cursor = conn.cursor()
    cursor.execute('SELECT product_name, username, feedback, rating FROM wb_feedback WHERE feedback_id in {}'.format(id_values))
    result = cursor.fetchall()
    print('Результат получения шести случайных записей -', *result)
    cursor.close()
    conn.close()
    return result
