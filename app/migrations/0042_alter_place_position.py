# Generated by Django 3.2.7 on 2021-12-02 12:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0041_auto_20211202_1757'),
    ]

    operations = [
        migrations.AlterField(
            model_name='place',
            name='position',
            field=models.IntegerField(blank=True, db_index=True, default=0, null=True, verbose_name='Позиция в рейтинге'),
        ),
    ]
