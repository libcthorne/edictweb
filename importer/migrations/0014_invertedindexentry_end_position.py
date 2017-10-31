# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-10-24 20:06
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('importer', '0013_auto_20171023_2034'),
    ]

    operations = [
        migrations.RunSQL(
            # entries prior to this migration have no known end position
            # and should be deleted
            "DELETE FROM importer_invertedindexentry;"
        ),
        migrations.AddField(
            model_name='invertedindexentry',
            name='end_position',
            field=models.PositiveIntegerField(),
        ),
    ]