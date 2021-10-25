import csv

from celery import shared_task
from django.http import StreamingHttpResponse


@shared_task
def add_task(x, y):
    return x+y

import time
import googlemaps
from googlemaps.exceptions import ApiError
import requests

from app.models import Query, Place, QueryPlace

KEY = 'AIzaSyAbOkxUWUw9z54up8AiMSCMX7rO7-8hqv8'
gmaps = googlemaps.Client(key=KEY)
detail_url = 'https://www.google.com/maps/place/?q=place_id:'
cid_to_place_id_url = 'https://maps.googleapis.com/maps/api/place/details/json?cid={0}&key='+KEY
photo_url = 'https://maps.googleapis.com/maps/api/place/photo?maxwidth={0}&photo_reference={1}&key={2}'
detail_url_for_api = 'https://maps.googleapis.com/maps/api/place/details/json?place_id={0}&key={1}'


def updateDetail(pk):
    place = Place.objects.filter(pk=pk).first()
    place_id = place.place_id
    url_api = detail_url_for_api.format(place_id, KEY)
    detail_data = requests.get(url_api)
    place.detail_data = detail_data.json()['result']
    place.save()


def create_query_place(place, query):
    query_place = QueryPlace.objects.filter(query=query).first()
    if query_place:
        query_place.place.add(place)
    else:
        query_place = QueryPlace.objects.create(query=query)
        query_place.save()
        query_place.place.add(place)


def searchDetail(place_id, query):
    url_api = detail_url_for_api.format(place_id, KEY)
    detail_data = requests.get(url_api)
    place = Place.objects.filter(place_id=place_id).first()
    if not place:
        place = Place.objects.create(place_id=place_id, detail_data=detail_data.json()['result'])
    else:
        place.detail_data = detail_data.json()['result']
    place.save()
    create_query_place(place, query)


def searchDetailList(places, detail, query_id):
    if detail:
        query = Query.objects.filter(pk=query_id).first()
        for place in places:
            searchDetail(place_id=place['place_id'], query=query)




def searchQuery(name, page_token='', page=1, detail=False, query_id=None):
    result_list = []
    try:
        time.sleep(2)
        response = gmaps.places(query=name, page_token=page_token)
        results = response['results']
        searchDetailList(results, detail, query_id)
        if page > 1 and 'next_page_token' in response:
            if response['next_page_token']:
                page_token = response['next_page_token']
            page -= 1
            next_page_result = searchQuery(name=name, page_token=page_token, page=page, detail=detail, query_id=query_id)

            result_list += results + next_page_result
            # print('Token: ', page_token)
            # print('Длина основного массива: ', len(result_list))
            # print('Длина малого массива: ', len(results))
            return result_list
        else:
            return results
    except ApiError as e:
        print(e)
        return []


@shared_task
def celery_parser(name, page_token='', page=1, detail=False, query_id=None):
    query = Query.objects.filter(id=query_id).first()
    data = []
    try:
        data = searchQuery(name=name, page_token=page_token, page=page, detail=detail, query_id=query_id)
    except:
        query.status = 'error'
        query.save()
    for q in data:
        place = Place.objects.filter(place_id=q['place_id']).first()
        if place:
            place.data = q
            place.save()
            create_query_place(place, query)
        else:
            place = Place.objects.create(place_id=q['place_id'], data=q)
            place.save()
            create_query_place(place, query)

    query.status = 'success'
    query.save()
    return 'Данные по запросу успешно сохранены: {}'.format(name)




# Парсер который я написал первым на Selenium
from selenium import webdriver
import csv
import time

from selenium.webdriver.chrome.options import Options

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

QUERY = 'отели+в+Астане'  # Запрос в поиске
URL = f'https://www.google.com/search?q={QUERY}&newwindow=1&tbm=lcl&sxsrf=AOaemvJF91rSXoO-Kt8Dcs2gkt9_JXLlCQ%3A1632305149583&ei=_f9KYayPI-KExc8PlcaGqA4&oq={QUERY}&gs_l=psy-ab.3...5515.12119.0.12483.14.14.0.0.0.0.0.0..0.0....0...1c.1.64.psy-ab..14.0.0....0.zLZdDbmH5so#rlfi=hd:;'
PAGE = 6  # Количество страниц для парсинга

def startFireFox():
    driver = webdriver.Firefox()
    driver.get(URL)
    return driver

def startChrome():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(URL)
    return driver


def google_parser():
    #driver = startChrome()
    driver = startChrome()
    for page in range(1, PAGE+1):
        # Проверяю сколько доступных страниц для клика, и если следующая страница есть в пагинации то происходит клик
        pagination = driver.find_element_by_class_name('AaVjTc')
        available_pages = pagination.find_elements_by_tag_name('td')
        for i in available_pages:
            if str(page) == i.text and page != 1:
                i.click()
                # После клика нужно ждать
                # чтобы не ставить на долгое время, использовал цикл, который при
                # изменении текущей страницы на следующую запустить парсинг страницы
                for j in range(20):
                    try:
                        pagination = driver.find_element_by_class_name('AaVjTc')
                        current_page = pagination.find_element_by_class_name('YyVfkd')
                        if current_page.text == str(page):
                            break
                    except:
                        pass
                    time.sleep(1)
                time.sleep(1)
                break

        print(f'СТРАНИЦА {page} начата')
        parse_page(driver, page)
        print(f'{page} страница готова')
        print('-----------------------------------')

    print('Парсинг завершен')
    driver.close()


# Все что ниже нужно для генерации CSV файла

def get_headers():
    return {
        'place_id': 'place_id',
        'name': 'name',
        'formatted_address': 'formatted_address',
        'rating': 'rating',
    }


def get_data(place):
    return {
        'place_id': place.place_id,
        'name': place.data['name'] if 'name' in place.data else '-',
        'formatted_address': place.data['formatted_address'] if 'formatted_address' in place.data else '-',
        'rating': place.data['rating'] if 'rating' in place.data else '-',
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
    response['Content-Disposition'] = 'attachment;filename=items.csv'
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
