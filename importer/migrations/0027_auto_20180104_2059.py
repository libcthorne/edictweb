# Generated by Django 2.0 on 2018-01-04 20:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('importer', '0026_dictionaryentry_frequency_rank'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='invertedindexentry',
            name='end_position',
        ),
        migrations.RemoveField(
            model_name='invertedindexentry',
            name='start_position',
        ),
    ]