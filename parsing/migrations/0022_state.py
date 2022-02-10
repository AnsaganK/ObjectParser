# Generated by Django 3.2.7 on 2022-02-09 15:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parsing', '0021_alter_faqquestion_options'),
    ]

    operations = [
        migrations.CreateModel(
            name='State',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=500)),
                ('svg', models.TextField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'State',
                'verbose_name_plural': 'States',
                'ordering': ['name'],
            },
        ),
    ]
