# Generated by Django 3.2.7 on 2021-11-24 19:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0031_alter_query_tags'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReviewType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Название типа')),
            ],
            options={
                'verbose_name': 'Тип отзыва',
                'verbose_name_plural': 'Типы отзывов',
                'ordering': ['-pk'],
            },
        ),
        migrations.RemoveField(
            model_name='review',
            name='rating',
        ),
        migrations.CreateModel(
            name='ReviewPart',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.IntegerField(choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)], default=1)),
                ('review', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='parts', to='app.review')),
                ('review_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to='app.reviewtype')),
            ],
            options={
                'verbose_name': 'Часть отзыва',
                'verbose_name_plural': 'Части отзыва',
                'ordering': ['-pk'],
            },
        ),
    ]