import telebot
from telebot import types
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from time import sleep
from random import shuffle

from wildberries_phrase import greet, no_feedback, wait_1, wait_2
from functions import waiting_element_to_show, filtering_products, check_adult, collect_feedback, finish_output_message, buttons_for_feedback
from db_functions import write_user_on_start, add_feedback, vote_for_feedback
from key import TOKEN

bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def start(message):
    # bot.send_message(message.chat.id, greet)
    write_user_on_start(message)
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    btn1 = types.KeyboardButton('Искать отзывы')
    btn2 = types.KeyboardButton('Не надо ничего искать')
    markup.row(btn1, btn2)
    bot.send_message(message.chat.id, greet, reply_markup=markup)


@bot.message_handler(content_types=['text'])
def choose_option(message):
    # сделать следующую строку короче, поместив все в кортеж
    if message.text == 'Искать отзывы' or message.text == 'Да! Ищем!':
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
    with webdriver.Chrome() as browser:
        try:
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
            bot.send_message(message.chat.id, 'Искать отзывы')

    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    btn1 = types.KeyboardButton('Да! Ищем!')
    btn2 = types.KeyboardButton('Не надо ничего искать')
    markup.row(btn1, btn2)
    buttons_for_feedback(markup, limit_to_six)
    bot.send_message(message.chat.id, 'Какой отзыв в этой подборке вы считаете самым неадекватным? Можете проголосовать или продолжить поиск среди этой цитадели истерик, малограмотности, отчаяния и "верните 100 рублей за возврат"', reply_markup=markup)
    bot.register_next_step_handler(message, to_vote_or_continue_searching, limit_to_six)


def to_vote_or_continue_searching(message, limit_to_six):
    '''функция голосования или продолжения поиска'''

    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    btn1 = types.KeyboardButton('Да! Ищем!')
    btn2 = types.KeyboardButton('Не надо ничего искать')
    markup.row(btn1, btn2)
    if message.text.isdigit() and 0 < int(message.text) <= len(limit_to_six):
        elem_index = int(message.text)-1
        vote_for_feedback(limit_to_six[elem_index])
        bot.send_message(message.chat.id, 'Ваш голос учтен и сохранен! Ищем дальше?', reply_markup=markup)
    elif message.text == 'Да! Ищем!' or message.text == 'Не надо ничего искать':
        choose_option(message)
    else:
        bot.send_message(message.chat.id, 'Я не понял ваш запрос. Давайте лучше попробуем найти какой-нибудь потрясный отзыв?!')


bot.polling(none_stop=True)
