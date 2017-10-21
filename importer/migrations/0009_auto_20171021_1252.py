# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-10-21 12:52
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('importer', '0008_pendingdictionaryimportrequest'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='dictionaryimportrequest',
            name='interrupted',
        ),
        migrations.RunSQL(
            # entries prior to this migration have no known import source
            # and should be deleted
            "DELETE FROM importer_dictionaryentry;"
        ),
        migrations.AddField(
            model_name='dictionaryentry',
            name='source_import_request',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='importer.DictionaryImportRequest'),
        ),
        migrations.AlterField(
            model_name='pendingdictionaryimportrequest',
            name='import_request',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='importer.DictionaryImportRequest'),
        ),
    ]
