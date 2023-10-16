from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from time import sleep, time


def waiting_element(browser, elem):
    """функция загрузки/готовности элемента"""
    WebDriverWait(
        browser, poll_frequency=0.5, timeout=10).until(
        EC.element_to_be_clickable((By.CLASS_NAME, elem))
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
