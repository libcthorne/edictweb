# Generated by Django 2.0 on 2018-01-03 20:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('importer', '0025_auto_20171231_1445'),
    ]

    operations = [
        migrations.AddField(
            model_name='dictionaryentry',
            name='frequency_rank',
            field=models.IntegerField(null=True),
        ),
    ]
