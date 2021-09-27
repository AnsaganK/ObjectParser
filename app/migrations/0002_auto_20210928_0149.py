# Generated by Django 3.2.7 on 2021-09-27 19:49

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='querytype',
            name='page',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='querytype',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Пользователь'),
        ),
        migrations.AlterField(
            model_name='query',
            name='data',
            field=models.JSONField(verbose_name='Данные JSON'),
        ),
        migrations.AlterField(
            model_name='query',
            name='place_id',
            field=models.TextField(verbose_name='Идентификатор в гугл картах'),
        ),
        migrations.AlterField(
            model_name='query',
            name='type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='queries', to='app.querytype', verbose_name='Запрос'),
        ),
        migrations.AlterField(
            model_name='querytype',
            name='name',
            field=models.CharField(max_length=1000, verbose_name='Название'),
        ),
    ]
