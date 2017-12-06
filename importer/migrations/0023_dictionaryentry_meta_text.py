# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-12-06 20:50
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('importer', '0022_invertedindexentry_index_column'),
    ]

    operations = [
        migrations.RunSQL(
            # entries prior to this migration have no meta_text
            # and should be deleted
            "DELETE FROM importer_dictionaryentry;"
        ),
        migrations.AddField(
            model_name='dictionaryentry',
            name='meta_text',
            field=models.CharField(max_length=2048),
        ),
    ]
