# Generated by Django 3.2.7 on 2021-12-14 09:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0047_tag_path'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tag',
            name='path',
            field=models.TextField(blank=True, null=True, unique=True, verbose_name='Путь'),
        ),
    ]
