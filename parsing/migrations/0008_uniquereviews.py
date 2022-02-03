# Generated by Django 3.2.7 on 2022-02-03 13:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('parsing', '0007_auto_20220203_1414'),
    ]

    operations = [
        migrations.CreateModel(
            name='UniqueReviews',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reviews_count', models.IntegerField(default=0)),
                ('reviews_checked', models.IntegerField(default=0)),
                ('place', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='parsing.place')),
                ('query', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='parsing.query')),
            ],
            options={
                'verbose_name': 'Unique review',
                'verbose_name_plural': 'Unique reviews',
                'ordering': ['-pk'],
            },
        ),
    ]
