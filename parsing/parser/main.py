import concurrent.futures
import time
from datetime import datetime
from enum import Enum
from typing import Optional

from selenium import webdriver
from selenium.webdriver.common.by import By

from constants import IS_VPS_SERVER
from .services.image_service import get_base_photo, GetPhotos
from .services.info_service import get_info
from .services.map_coordinates_service import get_coordinate
from .services.review_service import GetReviews
from .services.save_service import get_or_create_place, set_info, set_coordinate, set_photo_url, set_reviews, set_photos
from .services.start_driver_service import start_firefox, start_chrome
from .utils import error_catching, wait_and_get_element, function_error_catching
from ..models import CityService

# from .utils import save_image, deEmojify
# from .utils import city_service_create

INDEX = 0

SEARCH_URL = 'https://www.google.com/search?q={0}&newwindow=1&tbm=lcl&sxsrf=AOaemvJF91rSXoO-Kt8Dcs2gkt9_JXLlCQ%3A1632305149583&ei=_f9KYayPI-KExc8PlcaGqA4&oq={0}&gs_l=psy-ab.3...5515.12119.0.12483.14.14.0.0.0.0.0.0..0.0....0...1c.1.64.psy-ab..14.0.0....0.zLZdDbmH5so#rlfi=hd:;'
PLACE_DETAIL_PAGE_URL = 'https://maps.google.com/?cid={0}'


def strToInt(string):
    value = ''
    for i in string:
        try:
            number = int(i)
            value += i
        except:
            pass
    return int(value)


@error_catching('Начало парсинга')
def start_parsing(search_text: str, city: str, service: str, pages: Optional[int] = None):
    """ Начало парсинга: первая страница поисковой выдачи """
    display = None
    if IS_VPS_SERVER:
        from pyvirtualdisplay import Display
        display = Display(visible=False, size=(800, 600))
        display.start()
    driver = start_chrome(url=SEARCH_URL.format(search_text))
    # city_service = _get_city_service(city_service_id)
    page = 1
    while page <= pages if pages else True:
        is_page = _get_next_page(driver, page)
        if not is_page:
            break
        place_cids = _get_places_for_next_page(driver)
        create_places(place_cids, city, service)
        page += 1
    # _change_city_service_status(city_service, StatusChoices.SUCCESS)
    if display:
        display.stop()
    driver.close()


@error_catching('Переход на след. страницу')
def _get_next_page(driver: webdriver, page: int) -> bool:
    """ Проверяем есть ли след. страница, и если есть то берем список компании """
    if page == 1 or _get_pagination(driver, page):
        return True
    return False


@error_catching('Нажатие на кнопку след. страницы')
def _get_pagination(driver: webdriver, page: int) -> bool:
    """ Нажимаем на кнопку след. страницы (page: int), и возвращаем ответ в bool """
    pagination = wait_and_get_element(driver, 'AaVjTc')

    available_pages = pagination.find_elements(By.TAG_NAME, 'td')
    for available_page in available_pages:
        if str(page) == available_page.text and page != 1:
            available_page.click()
            time.sleep(3)
            return _get_current_page_number(driver, page)
    return False


@error_catching('Проверка изменения номера страницы в пагинации')
def _get_current_page_number(driver: webdriver, page: int) -> bool:
    """ Правдивость изменения номера страницы в элементе пагинации """
    pagination = driver.find_element(By.CLASS_NAME, 'AaVjTc')
    current_page = pagination.find_element(By.CLASS_NAME, 'YyVfkd')
    if current_page.text == str(page):
        return True
    return False


@error_catching('Получение всех CID со след. страницы')
def _get_places_for_next_page(driver: webdriver):
    """ После нажатия след. страницы в пагинации, получаем список компании на странице """
    cids = _get_cids_from_page_places(driver)
    return cids


@error_catching('Возврат списка CID со страницы списка компании')
def _get_cids_from_page_places(driver: webdriver) -> list[int]:
    """ Получить все CID компании с определенной страницы выдачи """
    cid_list = []
    time.sleep(1)
    places = driver.find_elements(By.CLASS_NAME, 'uMdZh')
    print(len(places))
    print()
    if not places:
        return cid_list
    for place in places:
        try:
            cid = place.find_element(By.CLASS_NAME, 'vwVdIc').get_attribute('data-cid')
            cid_list.append(cid)
        except:
            pass
    return cid_list


@error_catching('Массовое создание Place по их CID')
def create_places(cids: list[str], city: str, service: str):
    """ Массовое создание Place по их CID """
    print(cids)
    cids = cids[:3]
    for index, cid in enumerate(cids):
        cids[index] = {'cid': cid, 'city': city, 'service': service}
        _get_place(cids[index])
    # with concurrent.futures.ThreadPoolExecutor(max_workers=len(cids)) as executor:
    #     executor.map(_get_place, cids)


def _get_place(data: dict):
    """ Перейти на детальную страницу компании по CID, и создать объект Place """
    cid = data.get('cid')
    city = data.get('city')
    service = data.get('service')
    print('https://www.google.com/maps?cid=' + cid)
    place_create_driver(cid, city, service)


@error_catching('Открытие браузера для детальной компании')
def place_create_driver(cid: str, city: str, service: str):
    """ Открываем браузер для определенного Place по CID и получаем данные """
    start_time = datetime.now()
    url = PLACE_DETAIL_PAGE_URL.format(cid)
    driver = start_chrome(url=url)

    base_info = _get_base_info_from_place(driver)
    print(base_info)

    full_info = get_info(driver)
    print(full_info)

    coordinate = get_coordinate(driver)
    print(coordinate)

    base_photo = get_base_photo(driver)
    print(base_photo)

    reviews = GetReviews(driver).get_reviews() if base_info.get('rating_user_count') else []
    print(reviews)

    photos = GetPhotos(driver).get_photos()
    print(photos)

    print(datetime.now() - start_time)
    print()

    place_save(cid, city, service, base_info, full_info, coordinate, base_photo, reviews, photos)

    driver.close()


def place_save(cid, city, service, base_info, full_info, coordinate, base_photo, reviews, photos):
    place = get_or_create_place(
        base_info.get('title'),
        base_info.get('rating'),
        base_info.get('rating_user_count'),
        cid
    )
    place.city_service = CityService.objects.filter(city__name=city, service__name=service).first()
    place.save()

    print('base_photo: ', base_photo)

    print('palce_id: ', place.id)

    set_info(full_info, place)

    set_coordinate(coordinate, place)

    set_photo_url(base_photo, place.id, base=True)

    set_reviews(reviews, place)

    set_photos(photos, place.id)
    print(photos)
    print('Закрыто')


def _get_base_info_from_place(driver: webdriver) -> dict:
    classes = ['DUwDvf', 'x3AX1-LfntMc-header-title-title']
    title_class = classes[0]
    title = function_error_catching(
        func=lambda: wait_and_get_element(driver, f'{title_class}').get_attribute('innerText'),
        value='No name',
        message='Получение Title объекта компании'
    )

    rating = function_error_catching(
        func=lambda: wait_and_get_element(driver, 'jANrlb').find_element(By.TAG_NAME, 'div').get_attribute('innerText'),
        value='0',
        message='Получение Rating объекта компании'
    )
    rating = float(rating.replace(',', '.'))

    rating_user_count_classes = ['HHrUdb', 'Yr7JMdHHrUdb fontTitleSmall rqjGif']
    rating_user_count_class = rating_user_count_classes[0]
    rating_user_count = function_error_catching(
        func=lambda: wait_and_get_element(driver, f'{rating_user_count_class}').get_attribute('innerText'),
        value='0',
        message='Получение количества пользователей оставивших отзыв'
    )
    rating_user_count = strToInt(rating_user_count)

    return {
        'title': title,
        'rating': rating,
        'rating_user_count': rating_user_count,
    }


@error_catching('Изменения статуса хаба')
def _change_city_service_status(city_service, status):
    """ Изменить текущий статус на УСПЕШНО """
    pass


@error_catching('Получение объекта хаба')
def _get_city_service(city_service_id: int):
    pass
