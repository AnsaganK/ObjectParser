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

from app.models import Query, QueryType

KEY = 'AIzaSyAbOkxUWUw9z54up8AiMSCMX7rO7-8hqv8'
gmaps = googlemaps.Client(key=KEY)
detail_url = 'https://www.google.com/maps/place/?q=place_id:'
photo_url = 'https://maps.googleapis.com/maps/api/place/photo?maxwidth={0}&photo_reference={1}&key={2}'
detail_url_for_api = 'https://maps.googleapis.com/maps/api/place/details/json?place_id={0}&key={1}'


def searchDetailList(queries, detail, query_type_id):
    if detail:
        query_type = QueryType.objects.filter(pk=query_type_id).first()
        for query in queries:
            searchDetail(place_id=query['place_id'], query_type=query_type)


def searchDetail(place_id, query_type):
    url_api = detail_url_for_api.format(place_id, KEY)
    detail_data = requests.get(url_api)
    query = Query.objects.create(place_id=place_id, type=query_type, detail_data=detail_data.json()['result'])
    query.save()


def updateDetail(pk):
    query = Query.objects.filter(pk=pk).first()
    place_id = query.place_id
    url_api = detail_url_for_api.format(place_id, KEY)
    detail_data = requests.get(url_api)
    query.detail_data = detail_data.json()['result']
    query.save()

@shared_task
def celery_parser(name, page_token='', page=1, detail=False, query_type_id=None):
    query_type = QueryType.objects.filter(id=query_type_id).first()
    data = []
    try:
        data = searchQuery(name=name, page_token=page_token, page=page, detail=detail, query_type_id=query_type_id)
    except:
        query_type.status = 'error'
        query_type.save()
    for q in data:
        if detail:
            query = Query.objects.filter(place_id=q['place_id']).first()
            if query:
                query.data = q
                query.save()
            else:
                query = Query(place_id=q['place_id'], type=query_type, data=q)
                query.save()
        else:
            query = Query(place_id=q['place_id'], type=query_type, data=q)
            query.save()
    query_type.status = 'success'
    query_type.save()
    return 'Данные по запросу успешно сохранены: {}'.format(name)


def searchQuery(name, page_token='', page=1, detail=False, query_type_id=None):
    result_list = []
    try:
        time.sleep(2)
        response = gmaps.places(query=name, page_token=page_token)
        results = response['results']
        searchDetailList(results, detail, query_type_id)
        if page > 1 and 'next_page_token' in response:
            if response['next_page_token']:
                page_token = response['next_page_token']
            page -= 1
            next_page_result = searchQuery(name=name, page_token=page_token, page=page, detail=detail, query_type_id=query_type_id)

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


def get_headers():
    return {
        'place_id': 'place_id',
        'name': 'name',
        'formatted_address': 'formatted_address',
        'rating': 'rating',
    }

def get_data(query):
    return {
        'place_id': query.place_id,
        'name': query.data['name'] if 'name' in query.data else '-',
        'formatted_address': query.data['formatted_address'] if 'formatted_address' in query.data else '-',
        'rating': query.data['rating'] if 'rating' in query.data else '-',
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

def generate_file(file_name, queries):
    response = StreamingHttpResponse(
        streaming_content=(iter_items(queries, Echo())),
        content_type='text/csv',
    )
    response['Content-Disposition'] = 'attachment;filename=items.csv'
    return response
    response = StreamingHttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="data.csv"'

    writer = csv.writer(response, delimiter=',', lineterminator="\r")
    query_list = [['place_id', 'name', 'formatted_address', 'rating']]
    for query in queries:
        query_object = []
        query_object.append(query.place_id)
        query_object.append(query.data['name'] if 'name' in query.data else '-')
        query_object.append(query.data['formatted_address'] if 'formatted_address' in query.data else '-')
        query_object.append(query.data['rating'] if 'rating' in query.data else '-')
        query_list.append(query_object)
    writer.writerows(query_list)
    return response
