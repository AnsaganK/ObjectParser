# Generated by Django 3.2.7 on 2022-02-07 22:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parsing', '0015_city_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='cityservice',
            name='archive',
            field=models.BooleanField(default=False),
        ),
    ]