from typing import Optional

from selenium import webdriver
from selenium.webdriver.common.by import By

from ..utils import error_catching, wait_and_get_element
import time
import re


class GetPhotos:
    def __init__(self, driver):
        self.photo_list = []
        self.driver = driver

    @error_catching('Ошибка при получении фотографии')
    def get_photos(self):
        self._click_photo_button()
        time.sleep(3)
        self._scrolled_photos_block(count=2)
        time.sleep(1)
        photos = self._finds_photo_elements()
        photos = photos if photos else []
        print(len(photos))
        [self._check_photo(photo) for photo in photos]
        return self.photo_list

    @error_catching('Клик на кнопку все фото')
    def _click_photo_button(self):
        wait_and_get_element(self.driver, class_name='ofKBgf')
        self.driver.execute_script(
            'let photo_buttons = document.getElementsByClassName("ofKBgf"); '
            'photo_buttons[0].click();'
        )

    @error_catching('Скролл по блоку с картинками')
    def _scrolled_photos_block(self, count=1):
        scroll_block_classes = ['DxyBCb', 'siAUzd-neVct section-scrollbox cYB2Ge-oHo7ed cYB2Ge-ti6hGc']
        for i in range(1, count + 1):
            self.driver.execute_script(
                f'let q_12 = document.getElementsByClassName("DxyBCb")[0];'
                f'q_12.scrollTo(0, q_12.scrollHeight);')
            time.sleep(1)

    @error_catching('Получение объектов фотографии', None)
    def _finds_photo_elements(self):
        photos_block = wait_and_get_element(self.driver, class_name='DxyBCb')
        # photos = photos_block.find_elements_by_class_name('mWq4Rd-eEDwDf')
        photos = photos_block.find_elements(By.CLASS_NAME, 'U39Pmb')
        return photos

    @error_catching('Взятие детальной фотографии')
    def _check_photo(self, photo):
        photo = photo.get_attribute('innerHTML')
        pattern = r'(?<=image: url\(&quot;)(.+?)(?=&quot;\))'
        photo_url = re.search(pattern, photo)
        url = photo_url.group()
        if url[:2] == '//':
            url = url[2:]
        url = url.split('=')
        url.pop()
        url = ''.join(url)
        url = 'http://' + url if not url.startswith('http') else url
        self.photo_list.append(url)


@error_catching('Получение главного фото')
def get_base_photo(driver: webdriver) -> Optional[str]:
    """" Получаем главное фото через ссылку """
    photo_classes = ['aoRNLd', 'F8J9Nb-LfntMc-header-HiaYvf-LfntMc']
    photo = wait_and_get_element(driver, 'aoRNLd')
    button = photo.find_element(By.TAG_NAME, 'img')
    src = button.get_attribute('src')
    if len(src.split('=')) == 2:
        link = src.split('=')[0]
    else:
        link = src
    return link
