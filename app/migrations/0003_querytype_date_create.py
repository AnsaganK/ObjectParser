# Generated by Django 3.2.7 on 2021-09-27 20:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_auto_20210928_0149'),
    ]

    operations = [
        migrations.AddField(
            model_name='querytype',
            name='date_create',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]
