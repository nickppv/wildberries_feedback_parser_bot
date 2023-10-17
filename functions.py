from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from time import sleep


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
    print('получаем информацию об отзыве')
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

