# Generated by Django 3.2.7 on 2022-02-03 14:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('parsing', '0009_uniquereviews_date_create'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='UniqueReviews',
            new_name='UniqueReview',
        ),
    ]
