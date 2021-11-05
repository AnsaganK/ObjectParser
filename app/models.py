from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.shortcuts import reverse

# class Role(models.Model):
#     name = models.CharField(max_length=128, verbose_name='Название')
#
#     def __str__(self):
#         return self.name
from django.utils.text import slugify


class Query(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='queries', verbose_name='Пользователь')
    name = models.CharField(max_length=1000, verbose_name='Название')
    slug = models.SlugField(null=True, blank=True, unique=True)
    page = models.IntegerField(null=True, blank=True)
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
        return reverse('app:query_detail', args=[self.slug])

    @property
    def places_count(self):
        return Place.objects.filter(queries__query_id=self.id).count()

    @property
    def base_img(self):
        host = 'http://170.130.40.103'
        places = Place.objects.filter(queries__query_id=self.id)
        if len(places) > 0:
            place = places[0]
            if place and place.img:
                return f'{host}{place.img.url}'
        return f'{host}/static/img/not_found.png'

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
    name = models.CharField(max_length=1000, null=True, blank=True)
    slug = models.SlugField(max_length=1000, null=True, blank=True)
    cid = models.TextField(verbose_name='CID в гугл картах', null=True, blank=True, unique=True)
    img = models.ImageField(upload_to='place_images', null=True, blank=True, verbose_name='Картинка')
    img_url = models.TextField(null=True, blank=True)
    address = models.CharField(max_length=500, null=True, blank=True)
    phone_number = models.CharField(max_length=500, null=True, blank=True)
    site = models.CharField(max_length=1000, null=True, blank=True)
    description = models.CharField(max_length=500, null=True, blank=True)
    meta = models.TextField(null=True, blank=True)
    attractions = models.ManyToManyField('Attraction', related_name='places')

    rating = models.DecimalField(max_digits=2, decimal_places=1, null=True, blank=True)
    rating_user_count = models.IntegerField(null=True, blank=True, default=0)

    data = models.JSONField(null=True, blank=True, verbose_name='Данные JSON')
    detail_data = models.JSONField(null=True, blank=True, verbose_name='Детальные данные JSON')

    date_create = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    date_update = models.DateTimeField(auto_now=True, null=True, blank=True)

    isApiData = models.BooleanField(default=False)

    @property
    def get_rating(self):
        return self.data['rating'] if self.data and 'rating' in self.data else 0

    @property
    def get_name(self):
        return self.data['name'] if self.data and 'name' in self.data else '-'

    @property
    def locale_rating(self):
        return 1

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name = 'Объект'
        verbose_name_plural = 'Объекты'
        ordering = ['-pk']

    def get_absolute_url(self):
        return reverse('app:place_detail', args=[self.slug])

class PlacePhoto(models.Model):
    img = models.ImageField(upload_to='place_photos', null=True, blank=True)
    place = models.ForeignKey(Place, on_delete=models.CASCADE, null=True, blank=True, related_name='photos')

    def __str__(self):
        return self.id

    class Meta:
        verbose_name = 'Фотография'
        verbose_name_plural = 'Фотографии'


class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='reviews')
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='reviews')
    text = models.TextField()
    stars_choices = ((i, i) for i in range(1, 6))
    rating = models.IntegerField(default=5, choices=stars_choices)

    is_edit = models.BooleanField(default=False)
    date_create = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    date_update = models.DateTimeField(null=True, blank=True, auto_now=True)


    def __str__(self):
        return self.place.data['name']

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-pk']


class ReviewGoogle(models.Model):
    author_name = models.CharField(max_length=500, null=True, blank=True)
    rating = models.IntegerField(null=True, blank=True)
    text = models.TextField(null=True, blank=True)

    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='reviews_google')

    def __str__(self):
        return self.author_name

    class Meta:
        verbose_name = 'Отзыв с Google'
        verbose_name_plural = 'Отзывы с Google'

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


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
