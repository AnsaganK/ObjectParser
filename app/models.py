from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.shortcuts import reverse


class QueryType(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='query_types', verbose_name='Пользователь')
    name = models.CharField(max_length=1000, verbose_name='Название')
    page = models.IntegerField(null=True, blank=True)
    date_create = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Название запроса'
        verbose_name_plural = 'Названии запросов'
        ordering = ['-pk']

    def get_absolute_url(self):
        return reverse('query_type_detail', args=[self.id])

    @property
    def query_count(self):
        return self.queries.count()


class Query(models.Model):
    place_id = models.TextField(verbose_name='Идентификатор в гугл картах')
    data = models.JSONField(null=True, blank=True, verbose_name='Данные JSON')
    detail_data = models.JSONField(null=True, blank=True, verbose_name='Детальные данные JSON')
    type = models.ForeignKey(QueryType, null=True, blank=True, on_delete=models.CASCADE, related_name='queries', verbose_name='Запрос')

    def __str__(self):
        return self.place_id

    class Meta:
        verbose_name = 'Объект'
        verbose_name_plural = 'Объекты'
        ordering = ['-pk']

    def get_absolute_url(self):
        return reverse('query_detail', args=[self.id])


#
# @receiver(post_save, sender=User)
# def create_user_profile(sender, instance, created, **kwargs):
#     if created:
#         Profile.objects.create(user=instance)
#
#
# @receiver(post_save, sender=User)
# def save_user_profile(sender, instance, **kwargs):
#     instance.profile.save()
