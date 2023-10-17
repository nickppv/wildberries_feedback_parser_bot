import telebot
from fake_useragent import UserAgent
from telebot import types
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from time import sleep
from random import shuffle

from wildberries_phrase import greet, no_feedback, wait_1, wait_2
from functions import waiting_element_to_show, filtering_products, check_adult, collect_feedback
from key import TOKEN

bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start', 'привет'])
def start(message):
    # bot.send_message(message.chat.id, greet)
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    btn1 = types.KeyboardButton('Искать отзывы')
    btn2 = types.KeyboardButton('Не надо ничего искать')
    markup.row(btn1, btn2)
    bot.send_message(message.chat.id, greet, reply_markup=markup)


@bot.message_handler(content_types=['text'])
def choose_option(message):
    if message.text == 'Искать отзывы' or message.text == 'Да! Ищем!':
        bot.send_message(message.chat.id, 'Введите категорию или название товара для поиска.')
        bot.register_next_step_handler(message, search_actual_goods)
    elif message.text == 'Не надо ничего искать':
        bot.send_message(message.chat.id, 'Ну не надо так не надо. Не очень-то и хотелось.')


def search_actual_goods(message) -> list[str]:
    '''функция для поиска ссылок на товары с актуальными отзывами'''

    request = 'https://www.wildberries.ru/catalog/0/search.aspx?search=' + '%20'.join(message.text.lower().split())
    # успокаиваем пользователя, пишем что ждать осталось недолго
    bot.send_message(message.chat.id, wait_1)
    options = Options()
    # options.add_argument('--headless')
    with webdriver.Chrome(options=options) as browser:
        try:
            browser.get(request)
            # как только элемент становится доступен - прокручиваем страницу вниз
            waiting_element_to_show(browser, 'product-card-list')
            # прокручиваем страницу 14 раз чтобы получить все элементы
            [(browser.execute_script("window.scrollBy(0, 900)"), sleep(0.1)) for i in range(14)]
            all_goods_on_sheet = browser.find_elements(By.CLASS_NAME, 'j-card-item')
            # фильтруем записи без оценок, с оценкой 5 и повторяющиеся записи
            unique_links_list = filtering_products(all_goods_on_sheet)
            if unique_links_list:
                get_feedback(message, unique_links_list)
            else:
                bot.send_message(message.chat.id, 'Не получилось найти отзывы. Можно попробовать еще раз или немного изменить запрос')
        except Exception:
            bot.send_message(message.chat.id, 'Что-то пошло не так в поиске товара. Можно попробовать еще раз или немного изменить запрос.')
            bot.send_message(message.chat.id, 'Искать отзывы')


def get_feedback(message, links_list: list) -> str:
    '''получаем отзывы с одной звездой на товар'''

    shuffle(links_list)
    options = Options()
    # options.add_argument('--headless')
    with webdriver.Chrome(options=options) as browser:
        try:
            # переходим на страницу с товаром
            browser.get(links_list[0])
            browser.maximize_window()
            sleep(2)
            # ищем элементы, если есть проверка на возраст
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

        except Exception:
            bot.send_message(message.chat.id, 'Что-то пошло не так в поиске отзыва на товар. Можно попробовать еще раз или немного изменить запрос.\nИтак, что будем искать?')
            bot.register_next_step_handler(message, search_actual_goods)

        if len(minor_feedback) == 0:
            bot.send_message(message.chat.id, no_feedback)
        elif len(minor_feedback) > 5:
            bot.send_message(message.chat.id, f'Несколько отзывов о товаре "{minor_feedback[0][1]} {minor_feedback[0][0]}":')
            for i in range(5):
                bot.send_message(message.chat.id, f'<i>Покупатель{minor_feedback[i][2]} {minor_feedback[i][4]} написал гневный отзыв:</i> <b>"{minor_feedback[i][3]}"</b>', parse_mode='html')
        else:
            bot.send_message(message.chat.id, f'Несколько отзывов о товаре "{minor_feedback[0][1]} {minor_feedback[0][0]}"')
            for i in range(len(minor_feedback)):
                bot.send_message(message.chat.id, f'<i>Покупатель{minor_feedback[i][2]} {minor_feedback[i][4]} написал гневный отзыв:</i> <b>"{minor_feedback[i][3]}"</b>', parse_mode='html')
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        btn1 = types.KeyboardButton('Да! Ищем!')
        btn2 = types.KeyboardButton('Не надо ничего искать')
        markup.row(btn1, btn2)
        bot.send_message(message.chat.id, 'Будем искать еще?', reply_markup=markup)


bot.polling(none_stop=True)
