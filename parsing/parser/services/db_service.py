import json
import os

from ...models import CityService
from ...tasks import get_or_create_place, set_info, set_coordinate, set_photo_url, set_reviews, set_photos





# def place_save(cid, city, service, base_info, full_info, coordinate, base_photo, reviews, photos) -> dict:
#     data = dict()
#     data['cid'] = cid
#     data['base_info'] = base_info
#     data['full_info'] = full_info
#     data['coordinate'] = coordinate
#     data['base_photo'] = base_photo
#     data['reviews'] = reviews
#     data['photos'] = photos
#     city_path = f'cities/{city}'
#     service_path = f'{city_path}/{service}'
#     if not os.path.exists(city_path):
#         os.mkdir(city_path)
#     if not os.path.exists(service_path):
#         os.mkdir(service_path)
#
#     with open(f'{service_path}/{cid}.json', 'w') as f:
#         json.dump(data, f)
#             # with open(f'fake_db/{cid}.json', 'w') as f:
#             #     json.dump(data, f)
#     return data


def get_search_text():
    pass


def _get_current_city_service():
    pass


def change_current_city_service():
    pass
