# Generated by Django 3.2.7 on 2021-10-29 09:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0014_auto_20211029_1503'),
    ]

    operations = [
        migrations.AddField(
            model_name='place',
            name='img_url',
            field=models.TextField(blank=True, null=True),
        ),
    ]