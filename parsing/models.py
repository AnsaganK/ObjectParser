import re

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Count, Sum
from django.db.models.functions import Round, Length
from django.urls import reverse

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.shortcuts import reverse, redirect

# class Role(models.Model):
#     name = models.CharField(max_length=128, verbose_name='Название')
#
#     def __str__(self):
#         return self.name
from django.utils.text import slugify


class Tag(models.Model):
    name = models.CharField(max_length=1000, null=True, blank=True, unique=True)
    slug = models.SlugField(max_length=1000, null=True, blank=True)
    path = models.TextField(null=True, blank=True, unique=True, verbose_name='Путь')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'
        ordering = ['-pk']


class Query(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='queries',
                             verbose_name='User')
    name = models.CharField(max_length=1000, verbose_name='Название')
    slug = models.SlugField(null=True, blank=True, unique=True)
    sorted = models.BooleanField(default=False)
    page = models.IntegerField(null=True, blank=True)
    content = models.TextField(null=True, blank=True, verbose_name='Контент')
    tags = models.ManyToManyField(Tag, null=True, blank=True, related_name='queries')

    access = models.BooleanField(default=False)
    date_create = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    status_choices = (
        ('wait', 'wait'),
        ('success', 'success'),
        ('warning', 'warning'),
        ('error', 'error'),
    )
    status = models.CharField(choices=status_choices, default='success', max_length=100, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Название запроса'
        verbose_name_plural = 'Названии запросов'
        ordering = ['-pk']

    def get_absolute_url(self):
        return reverse('parsing:query_detail', args=[self.slug])

    @property
    def places_count(self):
        return Place.objects.filter(queries__query_id=self.id).count()

    @property
    def base_img(self):
        # host = 'http://170.130.40.103'
        places = Place.objects.filter(queries__query_id=self.id)
        if len(places) > 0:
            place = places[0]
            if place and place.img:
                return f'{place.img.url}'
        return '/static/img/not_found_place.png'


class QueryPlace(models.Model):
    query = models.ForeignKey(Query, on_delete=models.CASCADE, null=True, blank=True, related_name='places')
    place = models.ManyToManyField('Place', related_name='queries')

    def __str__(self):
        return f'{self.query.name}'

    class Meta:
        verbose_name = 'Запрос - Объект'
        verbose_name_plural = 'Запросы - Объекты'
        ordering = ['-pk']


class Place(models.Model):
    place_id = models.TextField(verbose_name='Идентификатор в гугл картах', null=True, blank=True)
    title = models.TextField(null=True, blank=True, default='', verbose_name='Title')
    name = models.CharField(max_length=1000, null=True, blank=True)
    slug = models.SlugField(max_length=1000, null=True, blank=True)
    cid = models.TextField(verbose_name='CID в гугл картах', null=True, blank=True, unique=True)
    img = models.ImageField(upload_to='place_images', null=True, blank=True, verbose_name='Картинка')
    img_url = models.TextField(null=True, blank=True)
    address = models.CharField(max_length=500, null=True, blank=True)
    phone_number = models.CharField(max_length=500, null=True, blank=True)
    site = models.CharField(max_length=1000, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    meta = models.TextField(null=True, blank=True, default='<meta>')
    attractions = models.ManyToManyField('Attraction', null=True, blank=True, related_name='places')
    coordinate_html = models.TextField(null=True, blank=True, verbose_name='Координаты')

    position = models.IntegerField(default=None, null=True, blank=True, db_index=True,
                                   verbose_name='Позиция в рейтинге')

    rating = models.DecimalField(max_digits=2, decimal_places=1, null=True, blank=True)
    rating_user_count = models.IntegerField(null=True, blank=True, default=0)

    data = models.JSONField(null=True, blank=True, verbose_name='Данные JSON')
    detail_data = models.JSONField(null=True, blank=True, verbose_name='Детальные данные JSON')

    date_create = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    date_update = models.DateTimeField(auto_now=True, null=True, blank=True)

    isApiData = models.BooleanField(default=False)

    is_redirect = models.BooleanField(default=False)
    redirect = models.TextField(null=True, blank=True, default='')

    @property
    def get_rating(self):
        return self.data['rating'] if self.data and 'rating' in self.data else 0

    def get_meta_description(self):
        if self.meta == None:
            return ' - '
        pattern = r'(?<=content=")(.+?)(?=")'
        meta = re.search(pattern, self.meta)
        if meta and meta.group():
            return meta.group()
        return ' - '

    @property
    def get_description(self):
        if self.description:
            return self.description
        return self.get_meta_description()

    @property
    def get_img(self):
        url = '/static/img/not_found_place.png'
        if self.img:
            url = self.img.url
        return url

    @property
    def isSite(self):
        if not self.site or self.site == ' - ':
            return ' - '
        if self.site[:4] == 'http':
            return self.site
        else:
            return 'http://' + self.site

    @property
    def get_name(self):
        return self.data['name'] if self.data and 'name' in self.data else '-'

    @property
    def locale_rating(self):
        return 1

    @property
    def get_more_text(self):
        queries = self.reviews.exclude(text=None).exclude(text='').annotate(text_len=Length('text')).order_by(
            '-text_len')
        if queries:
            return queries.first()
        return None

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name = 'Объект'
        verbose_name_plural = 'Объекты'
        ordering = ['-pk']

    def get_preview_url(self):
        return reverse('parsing:place_html_api', args=[self.cid])

    def get_absolute_url(self):
        return reverse('parsing:place_detail', args=[self.slug])


class PlacePhoto(models.Model):
    img = models.ImageField(upload_to='place_photos', null=True, blank=True)
    place = models.ForeignKey(Place, on_delete=models.CASCADE, null=True, blank=True, related_name='photos')

    def __str__(self):
        return self.id

    class Meta:
        verbose_name = 'Фотография'
        verbose_name_plural = 'Фотографии'


class ReviewType(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название типа')

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name = 'Тип отзыва'
        verbose_name_plural = 'Типы отзывов'
        ordering = ['-pk']


class ReviewPart(models.Model):
    review_type = models.ForeignKey(ReviewType, on_delete=models.CASCADE, related_name='reviews')
    review = models.ForeignKey('Review', on_delete=models.CASCADE, related_name='parts')
    stars_choices = ((i, i) for i in range(1, 6))
    rating = models.IntegerField(default=1, choices=stars_choices)

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name = 'Часть отзыва'
        verbose_name_plural = 'Части отзыва'
        ordering = ['-pk']


class Review(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.DO_NOTHING, related_name='reviews')
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='reviews')
    text = models.TextField()

    author_link = models.TextField(null=True, blank=True)
    author_name = models.CharField(max_length=500, null=True, blank=True)
    author_img_link = models.TextField(null=True, blank=True)
    author_img = models.ImageField(upload_to='google_avatars', null=True, blank=True)
    stars_choices = ((i, i) for i in range(1, 6))
    rating = models.IntegerField(default=1, choices=stars_choices, null=True, blank=True)

    is_edit = models.BooleanField(default=False)
    date_create = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    date_update = models.DateTimeField(null=True, blank=True, auto_now=True)

    is_google = models.BooleanField(default=False)

    is_dependent = models.BooleanField(default=False)
    dependent_choices = (
        ('VAeng', 'VAeng'),
        ('clarion', 'clarion'),
    )
    dependent_site = models.CharField(max_length=100, choices=dependent_choices, null=True, blank=True,
                                      verbose_name='Зависимый сайт')
    dependent_user_id = models.IntegerField(default=0, null=True, blank=True,
                                            verbose_name='ID пользователя на зависимом сайте')

    def __str__(self):
        return self.text[:30]

    @property
    def get_user_name(self):
        if self.user:
            return f'{self.user.profile.full_name}'
        return self.author_name

    @property
    def get_rating(self):
        if self.parts.exists():
            r = self.parts.all().aggregate(rating=Sum('rating'))
            c = self.parts.all().aggregate(count=Count('rating'))
            return round(r['rating'] / c['count'], 1)
        return self.rating

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-pk']


# class ReviewGoogle(models.Model):
#     author_name = models.CharField(max_length=500, null=True, blank=True)
#     rating = models.IntegerField(null=True, blank=True)
#     text = models.TextField(null=True, blank=True)
#
#     place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='reviews_google')
#     date_create = models.DateTimeField(null=True, blank=True, auto_now_add=True)
#     date_update = models.DateTimeField(null=True, blank=True, auto_now=True)
#
#     def __str__(self):
#         return self.author_name
#
#     class Meta:
#         verbose_name = 'Отзыв с Google'
#         verbose_name_plural = 'Отзывы с Google'
#         ordering = ['-text']


class AttractionImage(models.Model):
    url = models.URLField()
    img = models.ImageField(upload_to='attractions')

    def __str__(self):
        return self.url

    class Meta:
        verbose_name = 'Картинка достопримечательности'
        verbose_name_plural = 'Картинки'


class Attraction(models.Model):
    name = models.CharField(max_length=250)
    img = models.ForeignKey(AttractionImage, on_delete=models.DO_NOTHING, related_name='attractions')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Достопричательность'
        verbose_name_plural = 'Достопричательности'


class Location(models.Model):
    name = models.CharField(max_length=250)
    text = models.TextField(null=True, blank=True)
    rating = models.CharField(max_length=250, null=True, blank=True)

    place = models.OneToOneField(Place, related_name='location', on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Местоположение'
        verbose_name_plural = 'Местоположения'


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    img = models.ImageField(upload_to='user_avatars', null=True, blank=True)
    birth_date = models.DateTimeField(null=True, blank=True)
    gender_choices = (
        ('FEMALE', 'FEMALE'),
        ('MALE', 'MALE'),
    )
    gender = models.CharField(max_length=100, null=True, blank=True, choices=gender_choices, verbose_name='Гендер')

    @property
    def full_name(self):
        return f'{self.user.first_name} {self.user.last_name}'

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'
        ordering = ['-pk']


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
