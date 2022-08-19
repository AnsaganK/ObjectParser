import time

from selenium import webdriver
from selenium.webdriver.common.by import By

from ..utils import error_catching, function_error_catching, wait_and_get_element

coordinate_classes = ['zaxyGe', 's4ghve-AznF2e-ZMv3u-AznF2e']
coordinate_class = coordinate_classes[0]


@error_catching('Получение координат (карта)')
def get_coordinate(driver: webdriver):
    """ Нажимем на кнопку <<поделиться>> и из формы берем код карты """
    _click_button_share(driver)
    _wait_map_form(driver)
    _click_button_share_map(driver)
    input_coordinate = _wait_and_get_for_input_with_coordinates(driver)
    coordinate = input_coordinate.get_attribute('value')
    _close_map_form(driver)
    return coordinate


@error_catching('Поиск и нажатие на кнопку ПОДЕЛИТЬСЯ')
def _click_button_share(driver: webdriver):
    driver.execute_script('''
                    let share_buttons = document.getElementsByClassName('etWJQ jym1ob kdfrQc');
                    let share_button = share_buttons[share_buttons.length-1];
                    share_button.children[0].click();'''),


@error_catching('Ожидание появления формы с кнопками для переключения на вкладку копирования')
def _wait_map_form(driver: webdriver):
    wait_and_get_element(driver, class_name=coordinate_class, many=True)


@error_catching('Нажатие на кнопку ВСТРАИВАНИЕ КАРТ')
def _click_button_share_map(driver: webdriver):
    driver.execute_script(f'''
                    let card_button = document.getElementsByClassName('{coordinate_class}')[1];
                    card_button.click();''')


@error_catching('Получение input после перехода на вкладку с копированием кода карты')
def _wait_and_get_for_input_with_coordinates(driver: webdriver) -> webdriver:
    return wait_and_get_element(driver, class_name='m5XrEc').find_element(By.TAG_NAME, 'input')


@error_catching('Закрытие формы с копированием кода карт')
def _close_map_form(driver: webdriver):
    driver.execute_script('''
                    let coordinate_close_button = document.getElementsByClassName('AmPKde KzWhlc')[0];
                    coordinate_close_button.click();'''),
