# Generated by Django 3.2.7 on 2021-09-28 21:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0005_query_detail_data'),
    ]

    operations = [
        migrations.AlterField(
            model_name='query',
            name='data',
            field=models.JSONField(blank=True, null=True, verbose_name='Данные JSON'),
        ),
        migrations.AlterField(
            model_name='query',
            name='detail_data',
            field=models.JSONField(blank=True, null=True, verbose_name='Детальные данные JSON'),
        ),
    ]