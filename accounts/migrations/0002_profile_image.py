# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-04 14:34
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='image',
            field=models.ImageField(null=True, upload_to='uploads/'),
        ),
    ]
