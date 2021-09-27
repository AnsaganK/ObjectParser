import time
import googlemaps
from googlemaps.exceptions import ApiError

KEY = 'AIzaSyAbOkxUWUw9z54up8AiMSCMX7rO7-8hqv8'
gmaps = googlemaps.Client(key=KEY)
detail_url = 'https://www.google.com/maps/place/?q=place_id:ChIJp4JiUCNP0xQR1JaSjpW_Hms'


def searchDetail(place_id=''):
    url = detail_url+place_id


def searchQuery(name, page_token='', page=1):
    result_list = []
    try:
        time.sleep(2)
        if page > 1:
            response = gmaps.places(query=name, page_token=page_token)
            results = response['results']
            if response['next_page_token']:
                page_token = response['next_page_token']
            page -= 1
            next_page_result = searchQuery(name=name, page_token=page_token, page=page)

            result_list += results + next_page_result
            # print('Token: ', page_token)
            # print('Длина основного массива: ', len(result_list))
            # print('Длина малого массива: ', len(results))
            return result_list
        else:
            response = gmaps.places(query=name, page_token=page_token)
            results = response['results']
            return results
    except ApiError as e:
        print(e)
        return []


def main():
    query = 'Музеи в москве'
    searchQuery(query, page=3)



if __name__ == '__main__':
    main()
