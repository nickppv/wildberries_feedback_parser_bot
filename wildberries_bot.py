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
        bot.send_message(message.chat.id, 'Введите категорию или название товара для поиска. Выбор товаров огромный, поэтому искать можно всякое. Не стесняйтесь!')
        bot.register_next_step_handler(message, search_actual_goods)
    elif message.text == 'Не надо ничего искать':
        bot.send_message(message.chat.id, 'Ну не надо так не надо. Не очень-то и хотелось.')


def search_actual_goods(message) -> list[str]:
    '''функция для поиска ссылок на товары с актуальными отзывами'''
    dump_list: list = []
    unique_items_list: list = []
    counter_error = 0
    initial_request = message
    ua = UserAgent()
    request = 'https://www.wildberries.ru/catalog/0/search.aspx?search=' + '%20'.join(message.text.lower().split())
    # успокаиваем пользователя, пишем что ждать осталось недолго
    bot.send_message(message.chat.id, wait_1)
    options = Options()
    options.add_argument('--headless')
    options.add_argument(f'--user-agent={ua.random}')
    with webdriver.Chrome(options=options) as browser:
        try:
            browser.get(request)
            # как только элемент становится доступен - прокручиваем страницу вниз
            WebDriverWait(browser, poll_frequency=0.25, timeout=10).until(
                EC.element_to_be_clickable(
                    (By.CLASS_NAME, 'product-card--hoverable')))
            # прокурчиваем страницу 15 раз чтобы получить все элементы
            [(browser.execute_script("window.scrollBy(0, 900)"), sleep(0.1)) for i in range(14)]
            all_goods_on_sheet = browser.find_elements(By.CLASS_NAME, 'j-card-item')
            for i in all_goods_on_sheet[1::]:
                # фильтруем записи без оценок, с оценкой 5 и повторяющиеся записи
                a = i.find_element(By.CLASS_NAME, 'product-card__brand')
                b = i.find_element(By.CLASS_NAME, 'product-card__name')
                if (i.find_element(By.CLASS_NAME, 'product-card__count').text != 'Нет оценок' and
                    i.find_element(By.CLASS_NAME, 'address-rate-mini--sm').text != '5' and
                    int(i.find_element(By.CLASS_NAME, 'product-card__count').text.split()[0]) > 50 and
                    [a, b] not in dump_list):
                    # добавляем ссылку на этот элемент в список
                    item = i.find_element(By.CLASS_NAME, 'product-card__link').get_attribute('href')
                    dump_list.append([a, b])
                    unique_items_list.append(item)
            get_feedback(message, unique_items_list)
        except Exception:
            counter_error += 1
            if counter_error == 3:
                bot.send_message(message.chat.id, 'Что-то пошло не так в поиске товара. Можно попробовать еще раз или немного изменить запрос.\nИтак, что будем искать?')
                bot.register_next_step_handler(message, search_actual_goods)
            else:
                search_actual_goods(initial_request)


def get_feedback(message, links_list: list) -> str:
    '''получаем отзывы с одной звездой на товар'''
    minor_feedback = set()
    shuffle(links_list)
    ua = UserAgent()
    options = Options()
    options.add_argument(f'--user-agent={ua.random}')
    # переходим по ссылкам на каждый товар в списке
    with webdriver.Chrome(options=options) as browser:
        try:
            # переходим на страницу с товаром
            browser.get(links_list[0])
            # задаем ожидание доступности элемента
            WebDriverWait(browser, poll_frequency=0.5, timeout=10).until(
                EC.element_to_be_clickable(
                    (By.CLASS_NAME, 'product-page__grid')))
            browser.maximize_window()
            # успокаиваем пользователя, пишем что ему осталось еще немного
            bot.send_message(message.chat.id, wait_2)
            # получаем страницу с отзывами
            marks_sheet = browser.find_element(By.ID, 'comments_reviews_link').get_attribute('href')
            print(f'print(marks_sheet) - {marks_sheet}')
            browser.get(marks_sheet)
            # задаем ожидание доступности элемента
            WebDriverWait(browser, 10).until(
                EC.element_to_be_clickable(
                    (By.CLASS_NAME, "user-activity__tab-content")))
            # получаем название и общую информацию о товаре
            brand_name, general_name = map(
                lambda x: x.capitalize(), browser.find_element(
                    By.CLASS_NAME, 'product-line__name').text.split(' / '))
            # меняем порядок отзывов начиная с отрицательных
            [browser.find_element(By.CSS_SELECTOR, 'section>div>div>div>ul>li:nth-child(2)>a').click() for i in range(2)]
            # прокручиваем страницу отзывов двадцать+ раз вниз
            [(browser.execute_script("window.scrollBy(0, 900)"), sleep(0.1)) for i in range(10)]
            all_feedback_for_this_product = browser.find_elements(By.CLASS_NAME, 'j-feedback-slide')
            for feedback in all_feedback_for_this_product:
                x = feedback.find_element(By.CLASS_NAME, 'feedback__rating').get_attribute('class').split()
                if 'star1' == x[2]:
                    user_name = feedback.find_element(
                        By.CLASS_NAME, 'feedback__header').text
                    user_name = ', который не указал своего имени' if user_name == 'Покупатель Wildberries' else user_name
                    print(user_name)
                    feedback_text = feedback.find_element(
                        By.CLASS_NAME, 'feedback__text').text
                    print(feedback_text)
                    feedback_date = ' в '.join(feedback.find_element(
                        By.CLASS_NAME, 'feedback__date').text.split(', '))
                    print(feedback_date)
                minor_feedback.add((brand_name, general_name, user_name, feedback_text, feedback_date))
            minor_feedback = list(minor_feedback)

        except Exception:
            bot.send_message(message.chat.id, 'Что-то пошло не так в поиске отзыва на товар. Можно попробовать еще раз или немного изменить запрос.\nИтак, что будем искать?')
            bot.register_next_step_handler(message, search_actual_goods)

        if len(minor_feedback) == 0:
            bot.send_message(message.chat.id, no_feedback)
        elif len(minor_feedback) > 5:
            bot.send_message(message.chat.id, f'Несколько отзывов о товаре "{minor_feedback[0][1]} {minor_feedback[0][0]}":')
            for i in range(5):
                bot.send_message(message.chat.id, f'<i>Покупатель {minor_feedback[i][2]} {minor_feedback[i][4]} написал гневный отзыв:</i> <b>"{minor_feedback[i][3]}"</b>', parse_mode='html')
        else:
            bot.send_message(message.chat.id, f'Несколько отзывов о товаре "{minor_feedback[0][1]} {minor_feedback[0][0]}"')
            for i in range(len(minor_feedback)):
                bot.send_message(message.chat.id, f'<i>Покупатель {minor_feedback[i][2]} {minor_feedback[i][4]} написал гневный отзыв:</i> <b>"{minor_feedback[i][3]}"</b>', parse_mode='html')
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        btn1 = types.KeyboardButton('Да! Ищем!')
        btn2 = types.KeyboardButton('Не надо ничего искать')
        markup.row(btn1, btn2)
        bot.send_message(message.chat.id, 'Будем искать еще?', reply_markup=markup)


bot.polling(none_stop=True)
