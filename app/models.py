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

class Query(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='queries', verbose_name='Пользователь')
    name = models.CharField(max_length=1000, verbose_name='Название')
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
        return reverse('app:query_detail', args=[self.id])

    @property
    def places_count(self):
        return Place.objects.filter(queries__query_id=self.id).count()


# class QueryPlace(models.Model):
#     type = models.ManyToManyField(QueryType)
#     place = models.ManyToManyField('Query')
#
#     def __str__(self):
#         return self.pk

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
    place_id = models.TextField(verbose_name='Идентификатор в гугл картах', unique=True)
    data = models.JSONField(null=True, blank=True, verbose_name='Данные JSON')
    detail_data = models.JSONField(null=True, blank=True, verbose_name='Детальные данные JSON')
    # query = models.ForeignKey(Query, null=True, blank=True, on_delete=models.CASCADE, related_name='places', verbose_name='Запрос')
    date_create = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    date_update = models.DateTimeField(auto_now=True, null=True, blank=True)
    # rating = models.DecimalField(max_digits=2, decimal_places=1, null=True, blank=True)

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
        return self.place_id

    class Meta:
        verbose_name = 'Объект'
        verbose_name_plural = 'Объекты'
        ordering = ['-pk']

    def get_absolute_url(self):
        return reverse('app:place_detail', args=[self.place_id])


class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='reviews')
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='reviews')
    text = models.TextField()
    stars_choices = ((i, i) for i in range(1, 6))
    rating = models.IntegerField(max_length=100, default=5, choices=stars_choices)

    is_edit = models.BooleanField(default=False)
    date_create = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    date_update = models.DateTimeField(null=True, blank=True, auto_now=True)

    def __str__(self):
        return self.place.data['name']

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-pk']

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
