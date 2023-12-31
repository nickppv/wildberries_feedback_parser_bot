import telebot
from telebot.types import KeyboardButton as KB
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from time import sleep

from wildberries_phrase import no_feedback


def waiting_element_to_click(browser, elem):
    """функция загрузки/готовности элемента для клика"""
    WebDriverWait(
        browser, poll_frequency=0.5, timeout=10).until(
        EC.element_to_be_clickable((By.CLASS_NAME, elem))
        )


def waiting_element_to_show(browser, elem):
    """функция загрузки/готовности элемента"""
    WebDriverWait(
        browser, poll_frequency=0.5, timeout=10).until(
        EC.visibility_of_element_located((By.CLASS_NAME, elem))
        )


def filtering_products(all_goods_on_sheet):
    unique_links_list = []
    for i in all_goods_on_sheet:
        # количество отзывов
        feedback_count = i.find_element(By.CLASS_NAME, 'product-card__count').text.split()[0]
        if feedback_count.isdigit():
            feedback_count = int(feedback_count)
        else:
            continue
        # средняя оценка
        avg_grade = float(i.find_element(By.CLASS_NAME, 'address-rate-mini--sm').text)
        # ссылка на товар
        link = i.find_element(By.CLASS_NAME, 'product-card__link').get_attribute('href')
        # в условии добавляем эл-т в список в зависимости от кол-ва оценок и среднего балла
        # print(feedback_count, avg_grade, link)
        if avg_grade <= 4.7 and 30 < feedback_count < 250 and link not in unique_links_list:
            # добавляем ссылку на этот элемент в список
            unique_links_list.append(link)
        elif avg_grade <= 4.9 and feedback_count >= 150 and link not in unique_links_list:
            # добавляем ссылку на этот элемент в список
            unique_links_list.append(link)
    return unique_links_list


def check_adult(browser):
    '''проходим проверку на совершеннолетие'''

    adult_or_not = browser.find_elements(By.CLASS_NAME, 'popup__btn-main')
    if len(adult_or_not) == 2:
        # задаем ожидание, если появилось окошко подтверждения совершеннолетия
        adult_or_not[0].click()
        print('проходим проверку на совершеннолетие')


def collect_feedback(browser):
    '''получаем все отзывы с рейтингом единица (одна звезда)'''

    print('получаем брэнд и имя товара')
    brand_name, general_name = map(lambda x: x.capitalize(), browser.find_element(By.CLASS_NAME, 'product-line__name').text.split(' / '))
    # прокручиваем страницу отзывов десять+ раз вниз
    [(browser.execute_script("window.scrollBy(0, 900)"), sleep(0.1)) for i in range(10)]
    minor_feedback = set()
    all_feedback_for_this_product = browser.find_elements(By.CLASS_NAME, 'j-feedback-slide')
    for feedback in all_feedback_for_this_product:
        # ищем все отзывы и отсеиваем все больше 1-ой звезды
        feedback_rating = feedback.find_element(By.CLASS_NAME, 'feedback__rating').get_attribute('class').split()
        if 'star1' == feedback_rating[2]:
            username = feedback.find_element(
                By.CLASS_NAME, 'feedback__header').text
            username = ', который не указал своего имени,' if username == 'Покупатель Wildberries' else ' ' + username
            feedback_text = feedback.find_element(
                By.CLASS_NAME, 'feedback__text').text
            feedback_date = ' в '.join(feedback.find_element(
                By.CLASS_NAME, 'feedback__date').text.split(', '))
            print(username, feedback_date, brand_name, general_name, feedback_text)
        minor_feedback.add((brand_name, general_name, username, feedback_text, feedback_date))
    return list(minor_feedback)


def finish_output_message(minor_feedback, bot, message):
    '''функция вывода результатов поиска'''

    if len(minor_feedback) == 0:
        bot.send_message(message.chat.id, no_feedback)
    elif len(minor_feedback) > 5:
        bot.send_message(message.chat.id, f'Несколько отзывов о товаре "{minor_feedback[0][1]} {minor_feedback[0][0]}":')
        for i in range(6):
            bot.send_message(message.chat.id, f'<b>№{i+1}.</b> <i>Покупатель{minor_feedback[i][2]} {minor_feedback[i][4]} написал гневный отзыв:</i> <b>"{minor_feedback[i][3]}"</b>', parse_mode='html')
        return minor_feedback[:6]
    else:
        bot.send_message(message.chat.id, f'Несколько отзывов о товаре "{minor_feedback[0][1]} {minor_feedback[0][0]}"')
        for i in range(len(minor_feedback)):
            bot.send_message(message.chat.id, f'<b>№{i+1}.</b> <i>Покупатель{minor_feedback[i][2]} {minor_feedback[i][4]} написал гневный отзыв:</i> <b>"{minor_feedback[i][3]}"</b>', parse_mode='html')
        return minor_feedback


def buttons_for_feedback(markup, limit_to_six):
    '''создание кнопок для подборки отзывов с сайта WB'''

    markup.row(*[KB(i) for i in range(1, len(limit_to_six)+1)])
