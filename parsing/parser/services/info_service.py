from selenium import webdriver
from selenium.webdriver.common.by import By

from ..utils import wait_and_get_element, function_error_catching, error_catching, get_site
from bs4 import BeautifulSoup as BS


@error_catching('Сбор дополнительной информации о компании')
def get_info(driver: webdriver) -> dict:
    """ Берем данные по картинкам, определенной картинке соответсвуют определенные данные """
    data = {}
    data_names = {
        'https://www.gstatic.com/images/icons/material/system_gm/1x/place_gm_blue_24dp.png': 'address',
        'https://www.gstatic.com/images/icons/material/system_gm/2x/place_gm_blue_24dp.png': 'address',
        'https://www.gstatic.com/images/icons/material/system_gm/1x/phone_gm_blue_24dp.png': 'phone_number',
        'https://www.gstatic.com/images/icons/material/system_gm/2x/phone_gm_blue_24dp.png': 'phone_number',
        'https://www.google.com/images/cleardot.gif': 'location',
        'https://www.gstatic.com/images/icons/material/system_gm/1x/public_gm_blue_24dp.png': 'site',
        'https://www.gstatic.com/images/icons/material/system_gm/2x/public_gm_blue_24dp.png': 'site',
        'https://maps.gstatic.com/mapfiles/maps_lite/images/1x/ic_plus_code.png': 'plus_code',
        'https://maps.gstatic.com/mapfiles/maps_lite/images/2x/ic_plus_code.png': 'plus_code',
        'https://gstatic.com/local/placeinfo/schedule_ic_24dp_blue600.png': 'schedule',
    }

    data_objects = function_error_catching(
        func=lambda: wait_and_get_element(driver=driver, class_name='AeaXub', many=True),
        value=[],
        message='Взятие картинок для получения данных'
    )
    for i in data_objects:
        image_src = i.find_element(By.TAG_NAME, 'img').get_attribute('src')
        image_type = data_names.get(image_src)
        if image_type:
            data[image_type] = i.get_attribute('innerText')

    timetable_classes = ['eK4R0e', 'eK4R0e tfUnhc', 'y0skZc-jyrRxf-Tydcue']
    timetable_class = timetable_classes[0]
    timetable = function_error_catching(
        func=lambda: wait_and_get_element(driver, class_name=timetable_class, second=3).get_attribute(
            'innerHTML'),
        value='',
        message='Взятие расписания компании'
    )
    data['timetable'] = timetable
    return data


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
