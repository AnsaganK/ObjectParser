# Generated by Django 3.2.7 on 2021-12-17 17:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0050_auto_20211216_2129'),
    ]

    operations = [
        migrations.AlterField(
            model_name='place',
            name='redirect',
            field=models.TextField(blank=True, default='', null=True),
        ),
    ]
