# Generated by Django 3.2.7 on 2022-03-05 11:37

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parsing', '0028_alter_place_meta'),
    ]

    operations = [
        migrations.CreateModel(
            name='WordAiCookie',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cookies', django.contrib.postgres.fields.ArrayField(base_field=models.JSONField(), blank=True, null=True, size=None)),
                ('date_create', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Куки WordAi',
                'verbose_name_plural': 'Куки WordAi',
            },
        ),
        migrations.AddField(
            model_name='city',
            name='cities',
            field=models.ManyToManyField(blank=True, null=True, related_name='_parsing_city_cities_+', to='parsing.City'),
        ),
        migrations.AddField(
            model_name='city',
            name='zip_code',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
