from typing import Optional

from selenium import webdriver
from colorama import init, Fore, Back, Style
from selenium.common.exceptions import ElementClickInterceptedException

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import requests
from bs4 import BeautifulSoup as BS

import time

init(autoreset=True)


def get_site(url, timeout=None):
    if timeout:
        r = requests.get(url, timeout=timeout)
    else:
        r = requests.get(url)
    if r.status_code == 200:
        return r.text
    return None


def get_soup(html):
    if html:
        return BS(html, 'lxml')
    return html


def _show_error(message: str, e: Exception):
    print(Fore.LIGHTCYAN_EX + f"Ошибка в << {message} >>: " + e.__class__.__name__)


def error_catching(message: str, value=None):
    def my_decorator(func):
        def wrapped(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                _show_error(message, e)
                return value

        return wrapped

    return my_decorator


def function_error_catching(func, value=None, message: Optional[str] = None):
    try:
        return func()
    except Exception as e:
        _show_error(message, e) if message else None
        return value


def wait_and_get_element(driver: webdriver, class_name: str, second: int = 10, many: bool = False) -> webdriver:
    wait = WebDriverWait(driver, second)
    if many:
        wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, f'{class_name}')))
        return driver.find_elements(By.CLASS_NAME, class_name)
    else:
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, f'{class_name}')))
        return driver.find_element(By.CLASS_NAME, class_name)


def clicked_object(object, count=3):
    i = 0
    while i < count:
        try:
            object.click()
            return True
        except ElementClickInterceptedException:
            i += 1
            time.sleep(1)
    return False
