# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-04-22 20:24
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('osf_models', '0015_auto_20160422_1342'),
    ]

    operations = [
        migrations.AlterField(
            model_name='nodelog',
            name='date',
            field=models.DateTimeField(db_index=True),
        ),
    ]