import base64
import csv
import os
import io
from io import BytesIO
import random
from celery import shared_task
from django.contrib.auth.models import User, Group
from django.core.files import File
from django.core.files.base import ContentFile
from django.core.files.temp import NamedTemporaryFile
from django.http import StreamingHttpResponse
from mimesis import Person
from mimesis.enums import Gender
from pytils.translit import slugify

from .models import Place, Query, QueryPlace, PlacePhoto, Review, ReviewType, ReviewPart


@shared_task
def add_task(x, y):
    return x + y


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

# KEY = 'AIzaSyAbOkxUWUw9z54up8AiMSCMX7rO7-8hqv8'
# KEY = '0'
# CID_API_URL = 'https://maps.googleapis.com/maps/api/place/details/json?cid={0}&key='+KEY
CID_URL = 'https://maps.google.com/?cid={0}'

display = None


# gmaps = googlemaps.Client(key=KEY)

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


class GetPhotos:
    def __init__(self, driver):
        self.photo_list = []
        self.driver = driver

    def click_photo_button(self):
        try:
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'a4izxd-tUdTXb-xJzy8c-haAclf-UDotu')))
            self.driver.execute_script(
                'let photo_button = document.getElementsByClassName("a4izxd-tUdTXb-xJzy8c-haAclf-UDotu");photo_button[0].click()')
        except Exception as e:
            print('Ошибка при нажатии на кнопку ВСЕ ФОТО: ', e.__class__.__name__)

    def finds_photo_elements(self):
        try:
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'cYB2Ge-ti6hGc')))
            photos_block = self.driver.find_element_by_class_name('cYB2Ge-ti6hGc')
            photos = photos_block.find_elements_by_class_name('mWq4Rd-eEDwDf')
            print(len(photos))
            return photos
        except Exception as e:
            print('Ошибка при получении объектов фотографии: ', e.__class__.__name__)
            return None

    def check_photo(self, photo):
        try:
            photo = photo.get_attribute('innerHTML')
            pattern = r'(?<=image: url\(&quot;)(.+?)(?=&quot;\))'
            photo_url = re.search(pattern, photo)
            url = photo_url.group()
            if url[:2] == '//':
                url = url[2:]
            print(url)
            url = url.split('=')
            url.pop()
            url = ''.join(url)
            if not url.startswith('http'):
                url = 'http://' + url
            print(url)
            self.photo_list.append(url)
        except Exception as e:
            print('Ошибка при детальной фотографии: ', e.__class__.__name__)

    def get_photos(self):
        try:
            self.click_photo_button()
            time.sleep(3)
            photos = self.finds_photo_elements()
            print(len(photos))
            if photos:
                photos = photos[:5]
            for photo in photos:
                self.check_photo(photo)
            print(self.photo_list)
            return self.photo_list
        except Exception as e:
            print('Ошибка при получении фотографии: ', e.__class__.__name__)
            pass


def set_photos(photos_list, place_id):
    place = Place.objects.filter(id=place_id).first()
    place.photos.all().delete()
    for photo_url in photos_list:
        set_photo_url(photo_url, place_id, base=False)


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
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'F8J9Nb-LfntMc-header-HiaYvf-LfntMc')))
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


def set_photo_url(img_url, place_id, base=True):
    try:
        print(img_url)
        place = Place.objects.filter(id=place_id).first()
        if place and img_url:
            r = requests.get(img_url, timeout=10)
            if r.status_code == 200:
                content = r.content
                if base:
                    place.img_url = img_url
                    place.img.save(os.path.basename(img_url), ContentFile(content))
                    place.save()
                else:
                    photo = PlacePhoto(place=place)
                    photo.img.save(os.path.basename(img_url), ContentFile(content))
                    photo.save()
                return 'Фото назначено для {}'.format(place_id)
        return 'Фото не назначено {}'.format(place_id)
    except Exception as e:
        print(f'Ошиька при назначении фото: {img_url}', e.__class__.__name__)


def set_photo_review(img_url, review_id):
    try:
        review = Review.objects.filter(id=review_id).first()
        if review and img_url:
            r = requests.get(img_url, timeout=10)
            if r.status_code == 200:
                content = r.content
                review.author_img.save(os.path.basename(img_url), ContentFile(content))
                review.save()

    except Exception as e:
        print(e.__class__.__name__)


def set_photo_content(content, place_id, file_name='no_name'):
    place = Place.objects.filter(id=place_id).first()
    if not place:
        return None
    place_photo = PlacePhoto()
    place_photo.img.save(os.path.basename(file_name), ContentFile(content))
    place_photo.place = place
    place_photo.save()


def get_review_rating(review):
    try:
        rating = review.find_element_by_class_name('ODSEW-ShBeI-RGxYjb-wcwwM').get_attribute('innerText')
        rating = rating.split('/')
        available_rating = int(rating[-1])
        checked_rating = int(rating[0])
        if available_rating > 5:
            rating_coefficent = available_rating / 5
            checked_rating /= rating_coefficent
        rating = int(checked_rating)
    except:
        try:
            rating = len(review.find_elements_by_class_name('ODSEW-ShBeI-fI6EEc-active'))
        except Exception as e:
            print('Ошибка при получении звезд: ', e.__class__.__name__)
            rating = 1
    return rating


def review_more_button_click(driver, review):
    review_id = review.get_attribute('data-review-id')
    driver.execute_script(f'''
                            let review = document.querySelector("div[data-review-id={review_id}]");
                            let more = review.getElementsByClassName('ODSEW-KoToPc-ShBeI')[0].click();
                            ''')
    print('Review More Button Clicked')


def get_review_text(driver, review):
    try:
        try:
            review_more_button_click(driver, review)
            # wait = WebDriverWait(review, 10)
            # wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'ODSEW-KoToPc-ShBeI')))
            # more_text_button = review.find_element_by_class_name('ODSEW-KoToPc-ShBeI')
            # print(more_text_button.text)
            # clicked_object(more_text_button, 10)
            time.sleep(1)
            print('Нашел кнопку ЕЩЕ')
        except Exception as e:
            print('Не нашел кноаку ЕЩЕ: ', e.__class__.__name__)
            pass

        text = review.find_element_by_class_name('ODSEW-ShBeI-text').get_attribute('innerText')
    except Exception as e:
        text = ''
        print('Ошибка в отзыве: ', e.__class__.__name__)
    return text


class GetReviews:
    def __init__(self, driver):
        self.review_list = []
        self.driver = driver

    def get_page_review_button(self):
        try:
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'Yr7JMd-pane-hSRGPd')))
            review_button = self.driver.find_element_by_class_name('Yr7JMd-pane-hSRGPd')
            clicked_object(review_button, 10)
        except Exception as e:
            print('Ошибка при получении кнопки по отзывам', e.__class__.__name__)

    def get_reviews_objects(self):
        try:
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'ODSEW-ShBeI')))
            reviews = self.driver.find_elements_by_class_name('ODSEW-ShBeI')
            print(len(reviews))
            time.sleep(1)
            return reviews
        except Exception as e:
            print('-- Ошибка при получении первых отзывов', e.__class__.__name__)

    def scrolled_driver(self, ):
        try:
            self.driver.execute_script(
                'let a = document.getElementsByClassName("siAUzd-neVct section-scrollbox cYB2Ge-oHo7ed cYB2Ge-ti6hGc")[0];'
                'a.scrollTo(0, a.scrollHeight);')
            time.sleep(1)
            self.driver.execute_script(
                'let a = document.getElementsByClassName("siAUzd-neVct section-scrollbox cYB2Ge-oHo7ed cYB2Ge-ti6hGc")[0];'
                'a.scrollTo(0, a.scrollHeight);')
            time.sleep(1)
            reviews = self.get_reviews_objects()
            print('Всего загружено: ', len(reviews))
            random_number = random.randint(10, 20)
            reviews = reviews[:random_number]
            print(len(reviews))
            return reviews
        except Exception as e:
            print('--- Ошибка при скролле по отзывам')

    def check_review(self, review):
        try:
            rating = get_review_rating(review)
            text = get_review_text(self.driver, review)
            if text:
                self.review_list.append({
                    'rating': rating,
                    'text': text
                })
                return True
            return False
        except Exception as e:
            print('-- Ошибка при назначении атрибутов отзыву', e.__class__.__name__)
            time.sleep(1)
            return False

    def review_detail(self, review):
        try:
            exception = 0
            while exception < 3:
                checked = self.check_review(review)
                if checked:
                    break
                else:
                    exception += 1
        except Exception as e:
            print('Ошибка при получении детального отзыва', e.__class__.__name__)

    def close_review_pages(self):
        try:
            self.driver.execute_script(
                'let close_b = document.getElementsByClassName("VfPpkd-icon-Jh9lGc"); close_b[0].click()')
        except Exception as e:
            print('Ошибка при закрытии отзывов', e.__class__.__name__)

    def get_reviews(self):
        try:
            self.get_page_review_button()
            self.get_reviews_objects()
            reviews = self.scrolled_driver()
            for review in reviews:
                self.review_detail(review)
        except Exception as e:
            print('Ошибка при получении отзывов: ', e.__class__.__name__)
        self.close_review_pages()
        return self.review_list


#
# def get_this_page_reviews(driver):
#     review_list = []
#     try:
#         reviews = driver.find_elements_by_class_name('ODSEW-ShBeI')
#         for review in reviews:
#             try:
#                 author_name = review.find_element_by_class_name('ODSEW-ShBeI-title').get_attribute('innerText')
#             except:
#                 author_name = 'no_name'
#             rating = get_review_rating(review)
#             text = get_review_text(driver, review)
#             review_list.append({
#                 'author_name': author_name,
#                 'rating': rating,
#                 'text': text
#             })
#     except Exception as e:
#         print('Ошибка при получении отзывов', e.__class__.__name__)
#     return review_list


def set_review_parts(rating, review):
    for review_type in ReviewType.objects.all():
        review_part = ReviewPart.objects.update_or_create(review=review, review_type=review_type)[0]
        review_part.rating = rating
        review_part.save()


class GenerateUser():
    def __init__(self):
        pass

    def random_color(self):
        import random
        color = "#%06x" % random.randint(0, 0xFFFFFE)
        return color

    def generate_avatar(self, name_letters):
        from PIL import Image, ImageFont, ImageDraw
        width = 320
        height = 320
        img = Image.new('RGB', (width, height), color=(self.random_color()))
        draw_text = ImageDraw.Draw(img)
        font = ImageFont.truetype('parsing/static/parsing/fonts/Raleway-Regular.ttf', size=120)
        draw_text.text((width / 2, height / 2), name_letters, anchor='mm', font=font, fill=('#ffffff'))
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        return img_byte_arr

    def generate_data(self):
        person = Person('en')
        gender_choices = [Gender.FEMALE, Gender.MALE]
        random_gender = random.choice(gender_choices)
        email = person.email()

        full_name = person.full_name(gender=random_gender)
        username = full_name.replace(' ', '_')
        full_name = full_name.split(' ')
        first_name = full_name[0]
        last_name = full_name[-1]

        password = User.objects.make_random_password()

        user_data = {
            'username': username,
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'gender': random_gender.name,
            'password': password
        }
        return user_data

    def get_user(self):
        user_data = self.generate_data()
        name_letters = f'{user_data["first_name"][0]}.{user_data["last_name"][0]}'
        user_img = self.generate_avatar(name_letters)
        user_data['img'] = user_img
        return user_data

    def get_or_create_user(self):
        user_data = self.get_user()
        user = User.objects.get_or_create(username=user_data['username'])
        if not user[1]:
            return user[0]
        user = user[0]
        user.email = user_data['email']
        user.first_name = user_data['first_name']
        user.last_name = user_data['last_name']
        user.password = user_data['password']
        user.save()
        group = Group.objects.filter(name='User').first()
        if group:
            user.groups.add(group)
        user.profile.gender = user_data['gender']
        user.profile.img.save(os.path.basename(user.username) + '.png', ContentFile(user_data['img']))
        user.save()
        return user


def set_reviews(review_list, place):
    if len(review_list) == 0:
        return None
    try:
        place.reviews.all().delete()
        for review in review_list:
            user = GenerateUser().get_or_create_user()
            translate_word_1 = '(Translated by Google)'
            translate_word_2 = '(Original)'
            if translate_word_1 in review['text'] and translate_word_2 in review['text']:
                text = review['text'][len(translate_word_1)+1:review['text'].find(translate_word_2)-1]
            else:
                text = review['text']
            review = Review.objects.create(user=user,
                                           rating=review['rating'],
                                           text=text,
                                           place=place,
                                           is_google=True)
            review.save()
            try:
                set_review_parts(rating=review.rating, review=review)
            except Exception as e:
                print('Ошибка при назначении кусков отзыва', e)
    except Exception as e:
        print('Ошибка при назначении отзывов: ', e.__class__.__name__, e)


def get_or_create_place(name, rating, rating_user_count, cid):
    try:
        place = Place.objects.filter(cid=cid).first()
        if place:
            place.name = name
            place.rating = rating
            place.rating_user_count = rating_user_count
            place.save()
            return place
        place = Place.objects.create(name=name,
                                     rating=rating,
                                     rating_user_count=rating_user_count,
                                     cid=cid)
        place.save()
        place.slug = slugify(f'{place.name}-{str(place.id)}')
        place.save()
        return place
    except Exception as e:
        print('Ошибка при создании или взятии palce')
        print(e.__class__.__name__)


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
        print('Ошибка при взятии расписания: ', e.__class__.__name__)
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
    if not url or url == ' - ':
        return None
    url = 'http://' + url
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


def cid_to_place_id(cid):
    url = f'https://maps.googleapis.com/maps/api/place/details/json?cid={cid}&key={KEY}'
    print(url)
    r = requests.get(url)
    print(r)
    if r.status_code == 200 and r.json()['status'] == 'OK':
        print(r.json())
        return r.json()
    print('Ошибка ', url)
    return None


def get_coordinate(driver):
    try:
        time.sleep(1)
        print(1)
        driver.execute_script('''
                let share_buttons = document.getElementsByClassName('etWJQ etWJQ-text csAe4e-y1XlWb-QBLLGd vqxL8-haDnnc');
                let share_button = share_buttons[share_buttons.length-1];
                share_button.children[0].click();
        ''')
        print(2)
        time.sleep(1)
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 's4ghve-AznF2e-ZMv3u-AznF2e-uqeOfd')))
        driver.execute_script(
            '''
                let card_button = document.getElementsByClassName('s4ghve-AznF2e-ZMv3u-AznF2e NIyLF-haAclf s4ghve-AznF2e-ZMv3u-AznF2e-uqeOfd')[0];
                card_button.click();
            '''
        )
        print(3)
        wait2 = WebDriverWait(driver, 10)
        wait2.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'GALvsc-e1YmVc-map-YPqjbf')))
        input_coordinate = driver.find_element_by_class_name('GALvsc-e1YmVc-map-YPqjbf')
        coordinate = input_coordinate.get_attribute('value')
        print(4)
        driver.execute_script('''
                let coordinate_close_button = document.getElementsByClassName('OFhamd-LgbsSe OFhamd-LgbsSe-white-LkdAo')[0];
                coordinate_close_button.click();
        ''')
        return coordinate
    except Exception as e:
        print('Ошибка при взятии', e.__class__.__name__)
        return None


def set_coordinate(data, place):
    if data:
        place.coordinate_html = data
        place.save()


def place_update_driver(cid):
    pass


def place_create_driver(cid, query_id):
    url = CID_URL.format(cid)
    try:
        if IS_LINUX:
            driver = startChrome(url=url, path=CHROME_PATH)
        else:
            driver = startFireFox(url=url)
    except Exception as e:
        time.sleep(1)
        print('Не удалось открыть детальную страницу в боаузере: ', e.__class__.__name__)
        place_create_driver(cid, query_id)
        return None
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

        print(' --------- Беру координаты ')
        coordinate = get_coordinate(driver)
        set_coordinate(coordinate, place)

        print(' --------- Главное фото: ')
        base_photo = get_photo(driver)
        set_photo_url(base_photo, place.id, base=True)

        print(' --------- Отзывы: ')
        reviews = []
        # reviews = get_this_page_reviews(driver)
        if rating_user_count > 0:
            print('Отзывы со страницы отзывов')
            reviews = GetReviews(driver).get_reviews()
        print('Отзывы готовы', reviews)
        set_reviews(reviews, place)

        print(' --------- Фотографии')
        photos = GetPhotos(driver).get_photos()  # class PlacePhoto
        set_photos(photos, place.id)
        print(photos)

        print(title)
        print('Закрыто')
        print('----------------')

        driver.close()
    except Exception as e:
        print(e.__class__.__name__)
        print('Ошибка')
        driver.close()


def set_api_photos(photos, place_id):
    place = Place.objects.filter(id=place_id).first()
    if not place:
        return None
    place.photos.all().delete()
    photos = photos[:6]
    base = True
    for photo in photos:
        print(photo)
        photo_reference = photo['photo_reference']
        url = f'https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photo_reference={photo_reference}&key={KEY}'
        set_photo_url(img_url=url, place_id=place.id, base=base)
        base = False
        # image = gmaps.places_photo(photo_reference=photo_reference, max_width=width, max_height=height)
        # image_file = ''
        # for chunk in image:
        #     image_file += str(chunk)
        # image_file = base64.b64decode(image_file)
        # print(image_file)
        # set_photo_content(image_file, place_id=place.id, file_name=photo_reference)
    time.sleep(1)


def get_value_or_none(data, key, default_value=' - '):
    if key in data:
        return data[key]
    return default_value


def place_create_api(cid, query_id, api_data):
    name = get_value_or_none(api_data, 'name')
    address = get_value_or_none(api_data, 'formatted_address')
    phone_number = get_value_or_none(api_data, 'formatted_phone_number')
    rating = float(api_data['rating'] if 'rating' in api_data else 0)
    rating_user_count = float(api_data['user_ratings_total'] if 'user_ratings_total' in api_data else 0)
    site = get_value_or_none(api_data, 'website')
    place = Place.objects.filter(cid=cid).first()
    if not place:
        print('Такого объекта нет Создаю')
        place = Place.objects.create(cid=cid)
    place.name = name
    place.address = address
    place.phone_number = phone_number
    place.rating = rating
    place.rating_user_count = rating_user_count
    place.site = site
    place.isApiData = True
    place.save()
    place.slug = slugify(f'{name}-{str(place.id)}')
    place.save()

    query = Query.objects.filter(id=query_id).first()
    create_query_place(place, query)

    get_site_description.delay(site, place.id)

    print('Беру фотографии')
    photos = api_data['photos'] if 'photos' in api_data else []
    print(len(photos))
    set_api_photos(photos, place.id)

    print('Беру отзывы')
    reviews = api_data['reviews'] if 'reviews' in api_data else []
    set_reviews(reviews, place)


def place_detail(cid, query_id):
    place_create_driver(cid, query_id)


# def place_api_detail(cid):
#     url = CID_API_URL.format(cid)
#     r = requests.get(url)
#     if r.status_code == 200:
#         print(r.json())
#         if r.json()['status'] == 'OK':
#             result = r.json()['result']
#             print(result['place_id'], result['formatted_address'])
#         else:
#             print(r.json()['status'])
#     return None


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
        cid = place.find_element_by_class_name('C8TUKc').get_attribute('data-cid') if place.find_element_by_class_name(
            'C8TUKc') else None
        print('https://www.google.com/maps?cid=' + cid)
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
                        print('Ошибка в пагинации1: ', e.__class__.__name__)
                        # return False
                    time.sleep(1)
                time.sleep(1)
                break
        return False
    except Exception as e:
        print('Ошибка в пагинации2: ', e.__class__.__name__)
        return False


@shared_task
def startParsing(query_name, query_id, pages=None):
    display = None
    print(CUSTOM_URL.format(query_name))
    if IS_LINUX:
        # from xvfbwrapper import Xvfb
        # with Xvfb() as xvfb:
        #     display = xvfb.start()

        from pyvirtualdisplay import Display
        display = Display(visible=False, size=(800, 600))
        display.start()
        driver = startChrome(url=CUSTOM_URL.format(query_name), path=CHROME_PATH)
    else:
        driver = startFireFox(url=CUSTOM_URL.format(query_name))
    # print(1)
    # driver = startFireFox(url=CUSTOM_URL.format(query_name))

    # print(2)
    try:
        if pages:
            for page in range(1, pages + 1):
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
