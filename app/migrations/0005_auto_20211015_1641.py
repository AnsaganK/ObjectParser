# Generated by Django 3.2.7 on 2021-10-15 10:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0004_auto_20211014_1707'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='queryplace',
            name='query',
        ),
        migrations.AddField(
            model_name='queryplace',
            name='query',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='places', to='app.query', unique=True),
        ),
    ]
