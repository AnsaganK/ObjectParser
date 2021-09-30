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


def main():
    query = 'Музеи в москве'
    searchQuery(query, page=3)



if __name__ == '__main__':
    main()
