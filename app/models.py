from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse


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
    data = models.JSONField(verbose_name='Данные JSON')
    type = models.ForeignKey(QueryType, on_delete=models.CASCADE, related_name='queries', verbose_name='Запрос')

    def __str__(self):
        return self.place_id

    class Meta:
        verbose_name = 'Объект'
        verbose_name_plural = 'Объекты'
        ordering = ['-pk']

    def get_absolute_url(self):
        return reverse('query_detail', args=[self.id])
