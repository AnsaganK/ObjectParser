import csv
import os
from io import BytesIO

from celery import shared_task
from django.core.files import File
from django.core.files.base import ContentFile
from django.core.files.temp import NamedTemporaryFile
from django.http import StreamingHttpResponse

from .models import Place, Query, QueryPlace


@shared_task
def add_task(x, y):
    return x+y

from pip._vendor import requests
from selenium import webdriver
import csv
import time
from bs4 import BeautifulSoup as BS
from selenium.common.exceptions import ElementClickInterceptedException, StaleElementReferenceException, \
    NoSuchElementException, NoSuchAttributeException

from constants import CHROME_PATH, IS_LINUX
from datetime import datetime
import re
from selenium.webdriver.chrome.options import Options

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

INDEX = 0
FILE_NAME = 'hotels.csv'  # Назавние файла для сохранения
# QUERY = 'lawn care New york'  # Запрос в поиске
QUERY = 'Клининги москве'  # Запрос в поиске
URL = f'https://www.google.com/search?q={QUERY}&newwindow=1&tbm=lcl&sxsrf=AOaemvJF91rSXoO-Kt8Dcs2gkt9_JXLlCQ%3A1632305149583&ei=_f9KYayPI-KExc8PlcaGqA4&oq={QUERY}&gs_l=psy-ab.3...5515.12119.0.12483.14.14.0.0.0.0.0.0..0.0....0...1c.1.64.psy-ab..14.0.0....0.zLZdDbmH5so#rlfi=hd:;'
CUSTOM_URL = 'https://www.google.com/search?q={0}&newwindow=1&tbm=lcl&sxsrf=AOaemvJF91rSXoO-Kt8Dcs2gkt9_JXLlCQ%3A1632305149583&ei=_f9KYayPI-KExc8PlcaGqA4&oq={0}&gs_l=psy-ab.3...5515.12119.0.12483.14.14.0.0.0.0.0.0..0.0....0...1c.1.64.psy-ab..14.0.0....0.zLZdDbmH5so#rlfi=hd:;'

PAGE = 100  # Количество страниц для парсинга

KEY = 'AIzaSyAbOkxUWUw9z54up8AiMSCMX7rO7-8hqv8'
CID_API_URL = 'https://maps.googleapis.com/maps/api/place/details/json?cid={0}&key='+KEY
CID_URL = 'https://maps.google.com/?cid={0}'

display = None



def create_query_place(place, query):
    query_place = QueryPlace.objects.filter(query=query).first()
    if query_place:
        query_place.place.add(place)
    else:
        query_place = QueryPlace.objects.create(query=query)
        query_place.save()
        query_place.place.add(place)

def strToInt(string):
    value = ''
    for i in string:
        try:
            number = int(i)
            value += i
        except:
            pass
    return int(value)

def startFireFox(url=URL):
    driver = webdriver.Firefox()
    driver.get(url)
    return driver


def startChrome(url=URL, path=None):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-software-rasterizer")
    if path:
        driver = webdriver.Chrome(executable_path=path, options=chrome_options)
    else:
        driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)
    return driver


def clicked_object(object, count):
    i = 0
    while i < count:
        try:
            object.click()
            return True
        except ElementClickInterceptedException:
            i += 1
            time.sleep(1)
    return False


def is_find_object(parent_object, class_name):
    try:
        object = parent_object.find_element_by_class_name(class_name)
    except Exception as e:
        print('Ошибка при получении объекта в DOM: ', e.__class__.__name__)
        print(class_name)
        object = ''
    return object


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
        return BS(html)
    return html


def get_attractions(driver):
    attractions_list = []
    try:
        attractions = is_find_object(driver, 'xtu1r-K9a4Re-ibnC6b-haAclf')
        attractions = attractions.find_elements_by_class_name('NovK6')
        for attraction in attractions:
            pattern = r'(?<=image:url\(//)(.+?)(?=\))'
            attraction_img = attraction.get_attribute('innerHTML')
            attraction_img_url = re.search(pattern, attraction_img)
            attraction_text = attraction.get_attribute('innerText')
            attractions_list.append({'url': attraction_img_url.group(), 'text': attraction_text})
    except Exception as e:
        print('Ошибка при  получении достопримечательностей: ', e.__class__.__name__)
        return None
    print(attractions_list)
    return attractions_list


def get_photos(driver):
    try:
        photo_buttons = driver.find_elements_by_class_name('a4izxd-tUdTXb-xJzy8c-haAclf-UDotu')
        photo_buttons[0].click()
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'mWq4Rd-HiaYvf-CNusmb-gevUs')))
        photos = driver.find_elements_by_class_name('mWq4Rd-HiaYvf-CNusmb-gevUs')[:3]
        print(len(photos))
        time.sleep(3)
        for i in photos:
            print(i)
            print(i.get_attribute('innerHTML'))
            photo = i.find_element_by_class_name('mWq4Rd-HiaYvf-CNusmb-gevUs').get_attribute('innerHTML')
            pattern = r'(?<=image:url\(")(.+?)(?="\))'
            photo_url = re.search(pattern, photo)
            print(photo_url.group())
    except Exception as e:
        print('Ошибка при получении фотографии: ', e.__class__.__name__)
        pass


def get_place_information(driver):
    try:
        place_information = is_find_object(driver, 'uxOu9-sTGRBb-UmHwN')
        print(place_information.get_attribute('innerText'))
        return place_information.get_attribute('innerText')
    except Exception as e:
        print('Ошибка при получении описания места: ', e.__class__.__name__)
        return None

def get_location_information(driver):
    try:
        location_name = is_find_object(driver, 'exOO9c-V1ur5d')
        location_rating = is_find_object(driver, 'v10Rgb-v88uof-haAclf')
        location_text = is_find_object(driver, 'XgnsRd-HSrbLb-h3fvze-text')
        print(location_name.get_attribute('innerText'))
        print(location_rating.get_attribute('innerText'))
        print(location_text.get_attribute('innerText'))
    except Exception as e:
        print('Ошибка при получении информации о местности: ', e.__class__.__name__)
        return None

def get_photo(driver):
    try:
        photo = is_find_object(driver, 'F8J9Nb-LfntMc-header-HiaYvf-LfntMc')
        button = photo.find_element_by_tag_name('img')
        src = button.get_attribute('src')
        if len(src.split('=')) == 2:
            link = src.split('=')[0]
            print('Ссылка на главное фото: ', link)
        else:
            link = src
            print('Ссылка на главное фото: ', link)
        return link
    except Exception as e:
        print('Ошибка при получении главного фото: ', e.__class__.__name__)
        return None

def set_photo(img_url, place_id):
    place = Place.objects.filter(id=place_id).first()
    if place:
        r = requests.get(img_url)
        if r.status_code == 200:
            place.img_url = img_url
            img = r.content
            place.img.save(os.path.basename(img_url), ContentFile(img))
            place.save()
        return 'Фото назначено для {}'.format(place_id)
    return 'Фото не назначено {}'.format(place_id)


def get_reviews(driver):
    try:
        review_button = driver.find_element_by_class_name('Yr7JMd-pane-hSRGPd')
        clicked_object(review_button, 10)
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'ODSEW-ShBeI')))
        reviews = driver.find_elements_by_class_name('ODSEW-ShBeI')[:5]
        print(len(reviews))
        for review in reviews:
            print(review.get_attribute('innerHTML'))
            exception = 0
            print()
            while exception < 3:
                try:
                    try:
                        author_name = review.find_element_by_class_name('ODSEW-ShBeI-title').get_attribute('innerText')
                    except (NoSuchElementException, StaleElementReferenceException):
                        author_name = ''
                    try:
                        stars = review.find_element_by_class_name('ODSEW-ShBeI-RGxYjb-wcwwM').get_attribute('innerText')
                    except (NoSuchElementException, StaleElementReferenceException):
                        try:
                            stars = len(review.find_elements_by_class_name('ODSEW-ShBeI-fI6EEc-active'))
                        except Exception as e:
                            print('Ошибка при получении звезд: ', e.__class__.__name__)
                            stars = 'None'
                    try:
                        try:
                            # more_text_button = review.find_element_by_class_name('ODSEW-KoToPc-ShBeI')
                            # print(more_text_button.text)
                            # clicked_object(more_text_button, 10)
                            time.sleep(1)
                        except Exception as e:
                            print(e.__class__.__name__)
                            pass
                        # text = review.find_element_by_class_name('ODSEW-ShBeI-text')
                    except (NoSuchElementException, NoSuchAttributeException, StaleElementReferenceException):
                        text = ''
                        print('Ошибка')
                    print(author_name, stars)
                    break
                except StaleElementReferenceException:
                    exception += 1
                    print('Перехватил отзыв')
                    time.sleep(1)
    except Exception as e:
        print('Ошибка при получении отзывов: ', e.__class__.__name__)
        return None


def get_or_create_place(name, rating, rating_user_count, cid):
    place = Place.objects.filter(cid=cid).first()
    if place:
        place.name = name
        place.rating = rating
        place.rating_user_count = rating_user_count
        place.save()
        return place
    place = Place.objects.create(name=name, rating=rating, rating_user_count=rating_user_count, cid=cid)
    place.save()
    return place


def get_info(driver):
    data = {}
    data_names = {
        'https://www.gstatic.com/images/icons/material/system_gm/1x/place_gm_blue_24dp.png': 'address',
        'https://www.gstatic.com/images/icons/material/system_gm/2x/place_gm_blue_24dp.png': 'address',
        'https://www.gstatic.com/images/icons/material/system_gm/1x/phone_gm_blue_24dp.png': 'phone_number',
        'https://www.gstatic.com/images/icons/material/system_gm/2x/phone_gm_blue_24dp.png': 'phone_number',
        # 'https://www.gstatic.com/images/icons/material/system_gm/1x/schedule_gm_blue_24dp.png': 'timetable',
        # 'https://www.gstatic.com/images/icons/material/system_gm/2x/schedule_gm_blue_24dp.png': 'timetable',
        'https://www.google.com/images/cleardot.gif': 'location',
        'https://www.gstatic.com/images/icons/material/system_gm/1x/public_gm_blue_24dp.png': 'site',
        'https://www.gstatic.com/images/icons/material/system_gm/2x/public_gm_blue_24dp.png': 'site',
        'https://maps.gstatic.com/mapfiles/maps_lite/images/1x/ic_plus_code.png': 'plus_code',
        'https://maps.gstatic.com/mapfiles/maps_lite/images/2x/ic_plus_code.png': 'plus_code',
        'https://gstatic.com/local/placeinfo/schedule_ic_24dp_blue600.png': 'schedule',
    }
    try:
        timetable = driver.find_element_by_class_name('y0skZc-jyrRxf-Tydcue')
        timetable = timetable.get_attribute('innerText')
    except Exception as e:
        timetable = ''
        print(e.__class__.__name__)
    data['timetable'] = timetable
    try:
        data_objects = driver.find_elements_by_class_name('AeaXub')
        for i in data_objects:
            image_src = i.find_element_by_tag_name('img').get_attribute('src')
            try:
                image_type = data_names[image_src]
                print(image_type)
                data[image_type] = i.get_attribute('innerText')
                print(i.get_attribute('innerText'))
            except KeyError:
                pass
        return data
    except Exception as e:
        print('Ошибка при получении общих данных: ', e.__class__.__name__)
        return None

@shared_task()
def get_site_description(url, place_id):
    url = 'http://'+url
    meta_data = ''
    try:
        html = get_site(url, timeout=15)
    except:
        return f'Не взял Description {0}'.format(place_id)
    if not html:
        return html
    soup = BS(html, 'lxml')
    meta = soup.find('meta', attrs={'name': 'description'})
    if meta:
        meta_data = str(meta)
    place = Place.objects.filter(id=place_id).first()
    # print(url)
    # print(meta_data)
    if place:
        place.meta = meta_data
        place.save()
    return url

def set_info(data, place):
    if not data:
        return None
    if 'site' in data:
        place_id = place.id
        get_site_description.delay(url=data['site'], place_id=place_id)
    place.address = data['address'] if 'address' in data else None
    place.phone_number = data['phone_number'] if 'phone_number' in data else None
    place.site = data['site'] if 'site' in data else None
    place.save()

def place_detail(cid, query_id):
    url = CID_URL.format(cid)
    # driver = startChrome(url=url)
    driver = startChrome(url=url, path=CHROME_PATH)

    try:
        try:
            title = is_find_object(driver, 'x3AX1-LfntMc-header-title-title').get_attribute('innerText')
        except:
            title = 'No Name'
        try:
            rating = is_find_object(driver, 'aMPvhf-fI6EEc-KVuj8d').get_attribute('innerText')
            rating = float(rating.replace(',', '.'))
        except:
            rating = 0
        print(rating)
        try:
            rating_user_count = is_find_object(driver, 'Yr7JMd-pane-hSRGPd').get_attribute('innerText')
            rating_user_count = strToInt(rating_user_count)
        except:
            rating_user_count = 0
        print(rating_user_count)
        place = get_or_create_place(title, rating, rating_user_count, cid)
        query = Query.objects.filter(id=query_id).first()
        create_query_place(place, query)
        # rating =
        data = get_info(driver)
        print(data)
        set_info(data, place)
        print(' --------- Главное фото: ')
        base_photo = get_photo(driver)
        set_photo(base_photo, place.id)
        # print(' --------- Информация о месте: ')
        # place_information = get_place_information(driver)
        # print(' --------- Достопримечательности: ')
        # attractions = get_attractions(driver)                     # class Attraction - manyToMany
        # print(' --------- Информация о месте: ')
        # location_information = get_location_information(driver)     # class LocationInfo, class Location - ForeignKey
        # photos = get_photos(driver)                                 # class PlacePhoto
        # print(' --------- Отзывы: ')
        # reviews = get_reviews(driver)
        print(title, )
        print('Закрыто')
        print('----------------')

        driver.close()
    except Exception as e:
        print(e.__class__.__name__)
        print('Ошибка')
        driver.close()


def place_api_detail(cid):
    url = CID_API_URL.format(cid)
    r = requests.get(url)
    if r.status_code == 200:
        print(r.json())
        if r.json()['status'] == 'OK':
            result = r.json()['result']
            print(result['place_id'], result['formatted_address'])
        else:
            print(r.json()['status'])
    return None


# Функция которая парсит отели на странице
def parse_places(driver, query_id):
    time.sleep(3)
    try:
        places = driver.find_elements_by_class_name('uMdZh')
    except:
        return False
    print(len(places))
    if len(places) == 0:
        return False
    for place in places:
        cid = place.find_element_by_class_name('C8TUKc').get_attribute('data-cid') if place.find_element_by_class_name('C8TUKc') else None
        print('https://www.google.com/maps?cid='+cid)
        place_detail(cid, query_id) if cid else None
    return True

# Функция для смены страниц

def get_pagination(driver, page):
    try:
        pagination = is_find_object(driver, 'AaVjTc')
        available_pages = pagination.find_elements_by_tag_name('td')
        for i in available_pages:
            if str(page) == i.text and page != 1:
                i.click()
                # После клика нужно ждать
                # чтобы не ставить на долгое зкште(шьп), использовал цикл, который при
                # изменении текущей страницы на следующую запустить парсинг страницы
                for j in range(20):
                    try:
                        pagination = driver.find_element_by_class_name('AaVjTc')
                        current_page = pagination.find_element_by_class_name('YyVfkd')
                        if current_page.text == str(page):
                            return True
                    except Exception as e:
                        print('Ошибка в пагинации: ', e.__class__.__name__)
                        return False
                    time.sleep(1)
                time.sleep(1)
                break
        return False
    except Exception as e:
        print('Ошибка в пагинации: ', e.__class__.__name__)
        return False

@shared_task
def startParsing(query_name, query_id, pages=None):
    display = None
    if IS_LINUX:
        # from xvfbwrapper import Xvfb
        # with Xvfb() as xvfb:
        #     display = xvfb.start()

        from pyvirtualdisplay import Display
        display = Display(visible=False, size=(800, 600))
        display.start()

    # print(1)
    print(CUSTOM_URL.format(query_name))
    driver = startChrome(url=CUSTOM_URL.format(query_name), path=CHROME_PATH)
    # print(2)
    try:
        if pages:
            for page in range(1, pages+1):
                # Проверяю сколько доступных страниц для клика, и если следующая страница есть в пагинации то происходит клик
                if page == 1:
                    print(f'СТРАНИЦА {page} начата')
                    if not parse_places(driver, query_id):
                        break
                    print(f'{page} страница готова')
                    print('-----------------------------------')
                elif get_pagination(driver, page):
                    print(f'СТРАНИЦА {page} начата')
                    parse = parse_places(driver, query_id)
                    if not parse:
                        print('Возможно список не появился на этой странице')
                        break
                    print(f'{page} страница готова')
                    print('-----------------------------------')
            query = Query.objects.filter(id=query_id).first()
            query.status = 'success'
            query.save()
            print('Парсинг завершен')
            driver.close()
        else:
            page = 1
            while True:
                if page == 1:
                    print(f'СТРАНИЦА {page} начата')
                    if not parse_places(driver, query_id):
                        break
                    print(f'{page} страница готова')
                    print('-----------------------------------')
                elif get_pagination(driver, page):
                    print(f'СТРАНИЦА {page} начата')
                    parse = parse_places(driver, query_id)
                    if not parse:
                        print('Возможно список не появился на этой странице')
                        break
                    print(f'{page} страница готова')
                    print('-----------------------------------')
                else:
                    break
                page += 1
            query = Query.objects.filter(id=query_id).first()
            query.status = 'success'
            query.save()
            print('Парсинг завершен')
            driver.close()
    except Exception as e:
        print(e.__class__.__name__)
        if display:
            display.stop()
            # display.popen.terminate()

        driver.close()
        print('Критическая ошибка')

# Запуск скрипта
# def main():
#     query_name = 'name'
#     query_id = 1
#     pages = 4
#     print(1)
#     driver = startChrome(url=CUSTOM_URL.format(query_name), path=CHROME_PATH)
#     print(2)
#     try:
#         if pages:
#             for page in range(1, pages+1):
#                 # Проверяю сколько доступных страниц для клика, и если следующая страница есть в пагинации то происходит клик
#                 if page == 1:
#                     print(f'СТРАНИЦА {page} начата')
#                     parse_places(driver, query_id)
#                     print(f'{page} страница готова')
#                     print('-----------------------------------')
#                 elif get_pagination(driver, page):
#                     print(f'СТРАНИЦА {page} начата')
#                     parse_places(driver, query_id)
#                     print(f'{page} страница готова')
#                     print('-----------------------------------')
#             print('Парсинг завершен')
#             driver.close()
#         else:
#             page = 1
#             while True:
#                 if pages== 1:
#                     print(f'СТРАНИЦА {page} начата')
#                     if not parse_places(driver, query_id):
#                         break
#                     print(f'{page} страница готова')
#                     print('-----------------------------------')
#                 elif get_pagination(driver, page):
#                     print(f'СТРАНИЦА {page} начата')
#                     if not parse_places(driver, query_id):
#                         break
#                     print(f'{page} страница готова')
#                     print('-----------------------------------')
#                 page += 1
#             query = Query.objects.filter(id=query_id).first()
#             query.status = 'success'
#             query.save()
#             print('Парсинг завершен')
#             driver.close()
#     except Exception as e:
#         print(e.__class__.__name__)
#         if display:
#             display.stop()
#
#         driver.close()
#         print('Критическая ошибка')


# if __name__ == '__main__':
#     # startTime = datetime.now()
#     main()




# Все что ниже нужно для генерации CSV файла

def get_headers():
    return {
        'cid': 'cid',
        'name': 'name',
        'address': 'address',
        'rating': 'rating',
    }


def get_data(place):
    return {
        'cid': place.cid,
        'name': place.name,
        'address': place.address,
        'rating': place.rating,
    }


class Echo(object):
    def write(self, value):
        return value

def iter_items(items, pseudo_buffer):
    writer = csv.DictWriter(pseudo_buffer, fieldnames=get_headers())
    yield writer.writerow(get_headers())

    for item in items:
        yield writer.writerow(get_data(item))

def get_response(queryset):
    response = StreamingHttpResponse(
        streaming_content=(iter_items(queryset, Echo())),
        content_type='text/csv',
    )
    response['Content-Disposition'] = 'attachment;filename=items.csv'
    return response

def generate_file(file_name, places):
    response = StreamingHttpResponse(
        streaming_content=(iter_items(places, Echo())),
        content_type='text/csv',
    )
    response['Content-Disposition'] = f'attachment;filename={file_name}.csv'
    return response
    # response = StreamingHttpResponse(content_type='text/csv')
    # response['Content-Disposition'] = 'attachment; filename="data.csv"'
    #
    # writer = csv.writer(response, delimiter=',', lineterminator="\r")
    # query_list = [['place_id', 'name', 'formatted_address', 'rating']]
    # for query in queries:
    #     query_object = []
    #     query_object.append(query.place_id)
    #     query_object.append(query.data['name'] if 'name' in query.data else '-')
    #     query_object.append(query.data['formatted_address'] if 'formatted_address' in query.data else '-')
    #     query_object.append(query.data['rating'] if 'rating' in query.data else '-')
    #     query_list.append(query_object)
    # writer.writerows(query_list)
    # return response
