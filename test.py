from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from time import sleep


request = 'https://trial-sport.ru/'
# успокаиваем пользователя, пишем что ждать осталось недолго
options = Options()
# options.add_argument('--headless')
with webdriver.Chrome(options=options) as browser:
    browser.get(request)
    source_city = browser.find_element(By.CLASS_NAME, 'city_lnk')
    # меняем город на интернет-магазин
    if source_city.text != 'Интернет-магазин':
        source_city.click()
        browser.find_element(By.CSS_SELECTOR, '.yellow_block span').click()
        sleep(0.5)
    sleep(2)
    lst = browser.find_elements(By.CSS_SELECTOR, 'div>ul>li>div>div>div>a')
    lst[0].click()
    sleep(5)