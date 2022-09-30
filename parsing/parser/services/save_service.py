import io
import random

import requests
from django.contrib.auth.models import User, Group
from fake_useragent import UserAgent
from mimesis import Person
from mimesis.enums import Gender
from pytils.translit import slugify

from parsing.models import Place, PlacePhoto, ReviewPart, Review
from parsing.utils import save_image


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
        if User.objects.count() > 20:
            return User.objects.order_by('?').first()
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
        cloud_image = save_image(user_data['img'])
        user.profile.cloud_img = cloud_image
        user.save()
        return user


def get_or_create_place(name, rating, rating_user_count, cid):
    try:
        if Place.objects.filter(cid=cid).exists():
            place = Place.objects.filter(cid=cid).order_by('pk').first()

            # photos = place.photos.all()
            # reviews = place.reviews.all()

            print("PK: ", place.pk)
            place.pk = None
            place.city_service = None
            place.save()
            print(place.reviews)
            place.rating = rating
            place.rating_user_count = rating_user_count
            place.slug = slugify(f'{place.name}-{str(place.id)}')
            place.save()
            # if reviews:
            #     for base_review in reviews:
            #         review = Review.objects.get(pk=base_review.pk)
            #         review.pk = None
            #         review.place = place
            #         review.save()

            # if photos:
            #     for base_photo in photos:
            #         photo = PlacePhoto.objects.get(pk=base_photo.pk)
            #         photo.pk = None
            #         photo.place = place
            #         photo.save()
            place.archive = False
            place.save()
            return place, 0
        place = create_place(name, rating, rating_user_count, cid)
        return place, 1
    except Exception as e:
        print('Ошибка при создании или взятии palce')
        print(e.__class__.__name__)


def create_place(name, rating, rating_user_count, cid):
    place = Place.objects.create(name=name,
                                 rating=rating,
                                 rating_user_count=rating_user_count,
                                 cid=cid)
    place.save()
    place.slug = slugify(f'{place.name}-{str(place.id)}')
    place.save()
    return place


def set_info(data, place):
    if not data:
        return None
    if 'site' in data:
        place_id = place.id
        # get_site_description.delay(url=data['site'], place_id=place_id)
    place.address = data['address'] if 'address' in data else None
    place.phone_number = data['phone_number'] if 'phone_number' in data else None
    place.site = data['site'] if 'site' in data else None
    place.timetable = data['timetable'] if 'timetable' in data else None
    place.archive = False if place.city_service.city.name in str(place.address) else True

    place.save()


def set_coordinate(data, place):
    if data:
        place.coordinate_html = data
        place.save()


def set_photo_url(img_url, place_id, base=True):
    ua = UserAgent()
    try:
        # print('img url: ', img_url)
        print(Place.objects.filter(id=place_id).count())
        place = Place.objects.filter(id=place_id).first()
        if place and img_url:
            r = requests.get(img_url, timeout=10, headers={'User-Agent': ua.random})
            print(r.status_code)
            if r.status_code == 200:
                content = r.content
                cloud_image = save_image(content)
                if base:
                    # print('cloud image')
                    # print(place.cloud_img)
                    place.cloud_img = cloud_image
                    # print(place.cloud_img)
                    place.save()
                    # print(place.cloud_img)
                    # print('---- -----')
                else:
                    photo = PlacePhoto(place=place)
                    photo.cloud_img = cloud_image
                    photo.save()
                return 'Фото назначено для {}'.format(place_id)
        return 'Фото не назначено {}'.format(place_id)
    except Exception as e:
        print(f'Ошиька при назначении фото: {img_url}', e.__class__.__name__, e)
        print(e.__traceback__)


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
                text = review['text'][len(translate_word_1) + 1:review['text'].find(translate_word_2) - 1]
            else:
                text = review['text']
            review = Review.objects.create(user=user,
                                           rating=review['rating'],
                                           text=text,
                                           original_text=text,
                                           place=place)
            review.save()
            try:
                set_review_parts(rating=review.rating, review=review,
                                 review_types=place.city_service.review_types.all())
            except Exception as e:
                print('Ошибка при назначении кусков отзыва', e)
    except Exception as e:
        print('Ошибка при назначении отзывов: ', e.__class__.__name__, e)


def set_review_parts(rating, review, review_types=[]):
    for review_type in review_types:
        review_part = ReviewPart.objects.update_or_create(review=review, review_type=review_type)[0]
        review_part.rating = rating
        review_part.save()


def set_photos(photos_list, place_id):
    place = Place.objects.filter(id=place_id).first()
    place.photos.all().delete()
    for photo_url in photos_list:
        set_photo_url(photo_url, place_id, base=False)
