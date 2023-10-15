from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from time import sleep, time



def waiting_element(browser, elem):
    WebDriverWait(browser, poll_frequency=0.5, timeout=10).until(EC.element_to_be_clickable((By.CLASS_NAME, elem)))
