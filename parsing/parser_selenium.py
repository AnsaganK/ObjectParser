from selenium import webdriver
import csv
import time

from selenium.webdriver.chrome.options import Options

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from constants import geckodriver_path, chromedriver_path

URL = 'https://www.google.com/maps/place/?q=place_id:'


def startFireFox():
    driver = webdriver.Firefox(executable_path=geckodriver_path)
    return driver

def startChrome():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(executable_path=chromedriver_path, options=chrome_options)
    return driver


def time_sleep(action, returned=False):
    for i in range(20):
        try:
            data = action
            if returned:
                return data
            break
        except:
            pass
        time.sleep(1)
    return ''


def selenium_query_detail(place_ids=[]):
    #driver = webdriver.Firefox(executable_path=geckodriver_path)
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(executable_path=chromedriver_path, options=chrome_options)
    for place_id in place_ids:
        driver.get(URL+place_id)
        try:
            place_name = driver.find_element_by_class_name('QSFF4-text').text
        except:
            place_name = 'Название не найдено'

        try:
            place_info = driver.find_element_by_class_name('XgnsRd-HSrbLb-h3fvze-text').text
        except:
            place_info = 'Информация о месте не найдена'

        try:
            place_more_info = driver.find_element_by_class_name('BkFzcd-eTC1nf-MZArnb-text-NkyfNe').text
        except:
            place_more_info = 'Доп. информация не найдена'

        print(place_name)
        print(place_info)
        print(place_more_info)
        print('--------------------')
    driver.close()


if __name__ == '__main__':
    selenium_query_detail(['ChIJuTw8YUpLtUYRN1K7TAnYbF0', 'ChIJuTw8YUpLtUYRN1K7TAnYbF0', 'ChIJO2a8eO9KtUYRleo_a_zdDYg', 'ChIJ8wVkBC1LtUYReOJUwACYucc', 'ChIJuy2z6URKtUYR6r8oe8oJ9Mg'])

