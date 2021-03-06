# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-10-23 19:07
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('importer', '0011_auto_20171021_1336'),
    ]

    operations = [
        migrations.CreateModel(
            name='InvertedIndexEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_position', models.PositiveIntegerField()),
                ('dictionary_entry', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='importer.DictionaryEntry')),
            ],
        ),
        migrations.CreateModel(
            name='InvertedIndexWord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('word', models.CharField(max_length=128)),
            ],
        ),
        migrations.AddField(
            model_name='invertedindexentry',
            name='word',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='importer.InvertedIndexWord'),
        ),
    ]
