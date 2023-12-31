import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from selenium.webdriver.chrome.service import Service as ChromiumService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from time import sleep
from random import shuffle, randint

from wildberries_phrase import greet, wait_1, wait_2
from functions import waiting_element_to_show, filtering_products, check_adult, collect_feedback, finish_output_message, buttons_for_feedback
from db_functions import write_user_on_start, add_feedback, vote_for_feedback, get_the_most_terrible, get_count_db_records, get_random_records
from key import TOKEN

bot = telebot.TeleBot(TOKEN)


@bot.message_handler(func=lambda message: message.text == 'start')
@bot.message_handler(commands=['start'])
def start(message):
    # bot.send_message(message.chat.id, greet)
    write_user_on_start(message)
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    btn1 = KeyboardButton('Искать отзывы на сайте WB')
    btn2 = KeyboardButton('Случайная подборка из БД')
    btn3 = KeyboardButton('Шесть самых упоротых записей')
    btn4 = KeyboardButton('Не надо ничего искать')
    markup.row(btn1, btn2)
    markup.row(btn3, btn4)
    bot.send_message(message.chat.id, greet, reply_markup=markup)


@bot.message_handler(func=lambda message: message.text in ('Искать отзывы на сайте WB', 'Не надо ничего искать'))
def choose_option(message):
    if message.text in ('Искать отзывы на сайте WB'):
        bot.send_message(message.chat.id, 'Введите категорию или название товара для поиска.')
        bot.register_next_step_handler(message, search_actual_goods)
    elif message.text == 'Не надо ничего искать':
        bot.send_message(message.chat.id, 'Ну не надо так не надо. Не очень-то и хотелось.')


def search_actual_goods(message) -> list[str]:
    '''функция для поиска ссылок на товары с актуальными отзывами'''
    limit_to_six = []
    request = 'https://www.wildberries.ru/catalog/0/search.aspx?search=' + '%20'.join(message.text.lower().split())
    # успокаиваем пользователя, пишем что ждать осталось недолго
    bot.send_message(message.chat.id, wait_1)
    try:
        with webdriver.Chrome(service=ChromiumService(ChromeDriverManager().install())) as browser:
            browser.get(request)
            # как только элемент становится доступен - прокручиваем страницу вниз
            waiting_element_to_show(browser, 'product-card-list')
            # прокручиваем страницу 14 раз чтобы получить все элементы
            [(browser.execute_script("window.scrollBy(0, 900)"), sleep(0.05)) for i in range(14)]
            all_goods_on_sheet = browser.find_elements(By.CLASS_NAME, 'j-card-item')
            # фильтруем записи без оценок, с оценкой 5 и повторяющиеся записи
            unique_links_list = filtering_products(all_goods_on_sheet)
            if unique_links_list:
                shuffle(unique_links_list)
                browser.get(unique_links_list[0])
                browser.maximize_window()
                sleep(2)
                check_adult(browser)
                # ожидаем загрузки страницы с конкретным товаром
                waiting_element_to_show(browser, 'product-page__grid')
                # успокаиваем пользователя, пишем что ему осталось еще немного
                bot.send_message(message.chat.id, wait_2)
                # получаем страницу с отзывами
                marks_sheet = browser.find_element(By.ID, 'comments_reviews_link').get_attribute('href')
                browser.get(marks_sheet)
                print('получили страницу с отзывами')
                sleep(2)
                check_adult(browser)
                # задаем ожидание доступности элемента
                waiting_element_to_show(browser, 'product-feedbacks__main')
                # меняем порядок отзывов начиная с отрицательных
                [browser.find_element(By.CSS_SELECTOR, 'section>div>div>div>ul>li:nth-child(2)>a').click() for i in range(2)]
                # получаем все отзывы
                minor_feedback = collect_feedback(browser)
                limit_to_six = finish_output_message(minor_feedback, bot, message)
                add_feedback(minor_feedback)
            else:
                bot.send_message(message.chat.id, 'Не получилось найти отзывы. Можно попробовать еще раз или немного изменить запрос')
    except Exception:
        bot.send_message(message.chat.id, 'Что-то пошло не так в поиске товара. Можно попробовать еще раз или немного изменить запрос.')
        bot.send_message(message.chat.id, 'Искать отзывы на сайте WB')

    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    btn1 = KeyboardButton('Искать отзывы на сайте WB')
    btn2 = KeyboardButton('Случайная подборка из БД')
    btn3 = KeyboardButton('Шесть самых упоротых записей')
    btn4 = KeyboardButton('Не надо ничего искать')
    buttons_for_feedback(markup, limit_to_six)
    markup.row(btn1, btn2)
    markup.row(btn3, btn4)
    bot.send_message(message.chat.id, 'Какой отзыв в этой подборке вы считаете самым неадекватным? Можете проголосовать или продолжить поиск среди этой цитадели истерик, малограмотности, отчаяния и "верните 100 рублей за возврат"', reply_markup=markup)
    bot.register_next_step_handler(message, to_vote_or_continue_searching, limit_to_six)


def to_vote_or_continue_searching(message, limit_to_six):
    '''функция голосования или продолжения поиска'''

    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    btn1 = KeyboardButton('Искать отзывы на сайте WB')
    btn2 = KeyboardButton('Случайная подборка из БД')
    btn3 = KeyboardButton('Шесть самых упоротых записей')
    btn4 = KeyboardButton('Не надо ничего искать')
    markup.row(btn1, btn2)
    markup.row(btn3, btn4)
    # в условии определяем за какой номер отдаем голос или же продолжаем поиск
    if message.text.isdigit() and 0 < int(message.text) <= len(limit_to_six):
        elem_index = int(message.text)-1
        vote_for_feedback(limit_to_six[elem_index])
        bot.send_message(message.chat.id, 'Ваш голос учтен и сохранен! Ищем дальше?', reply_markup=markup)
    elif message.text in ('Продолжить поиск на сайте WB', 'Не надо ничего искать'):
        choose_option(message)
    elif message.text == 'Шесть самых упоротых записей':
        get_the_most_terrible_and_vote(message)
    elif message.text == 'Случайная подборка из БД':
        get_random_records_from_db_and_vote(message)
    elif message.text in ('/start', 'start'):
        start(message)
    else:
        bot.send_message(message.chat.id, 'Я не понял ваш запрос. Давайте лучше попробуем найти какой-нибудь потрясный отзыв?!')


@bot.message_handler(func=lambda message: message.text == 'Шесть самых упоротых записей')
def get_the_most_terrible_and_vote(message):
    '''получить шесть записей с высшим рейтингом'''

    result = get_the_most_terrible()
    for i in result:
        bot.send_message(message.chat.id, f'<b>Место №{result.index(i)+1}. Рейтинг: {i[3]}: {i[0]}</b>\n<i>Покупатель{i[1]} написал гневный отзыв:</i>\n<b>"{i[2]}"</b>', parse_mode='html')
    print(*result, sep='\n')
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    btn1 = KeyboardButton('Искать отзывы на сайте WB')
    btn2 = KeyboardButton('Случайная подборка из БД')
    btn3 = KeyboardButton('Не надо ничего искать')

    buttons_for_feedback(markup, result)
    markup.row(btn1)
    markup.row(btn2)
    markup.row(btn3)
    bot.send_message(message.chat.id, 'Какой отзыв в этой подборке вы считаете самым неадекватным? Можете проголосовать или продолжить поиск среди этой цитадели истерик, малограмотности, отчаяния и "верните 100 рублей за возврат"', reply_markup=markup)
    bot.register_next_step_handler(message, to_vote_or_continue_searching, result)


@bot.message_handler(func=lambda message: message.text == 'Случайная подборка из БД')
def get_random_records_from_db_and_vote(message):
    '''функция для получения шести случайных записей из бд'''

    random_num_lst = []
    # получаем общее количество записей в БД
    count_result = get_count_db_records()
    # на основании количества записей, выбираем шесть случайных в БД
    [random_num_lst.append(randint(1, count_result+1)) for i in range(6)]
    random_num_lst = tuple(random_num_lst)
    random_records = get_random_records(random_num_lst)
    for i in random_records:
        bot.send_message(message.chat.id, f'№{random_records.index(i)+1}. Покупатель<i>{i[1]}</i> оставил(а) о товаре: "{i[0]}" такой отзыв: <b>"{i[2]}"</b>.\nРейтинг у отзыва на данный момент: {i[3]}', parse_mode='html')
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    btn1 = KeyboardButton('Искать отзывы на сайте WB')
    btn2 = KeyboardButton('Случайная подборка из БД')
    btn3 = KeyboardButton('Шесть самых упоротых записей')
    btn4 = KeyboardButton('Не надо ничего искать')

    buttons_for_feedback(markup, random_records)
    markup.row(btn1)
    markup.row(btn2)
    markup.row(btn3)
    markup.row(btn4)
    bot.send_message(message.chat.id, 'Какой отзыв в этой подборке вы считаете самым неадекватным? Можете проголосовать или продолжить поиск среди этой цитадели истерик, малограмотности, отчаяния и "верните 100 рублей за возврат"', reply_markup=markup)
    bot.register_next_step_handler(message, to_vote_or_continue_searching, random_records)


bot.polling(none_stop=True)
