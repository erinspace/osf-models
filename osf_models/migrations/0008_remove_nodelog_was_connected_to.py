# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-05-18 23:52
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('osf_models', '0007_auto_20160518_1848'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='nodelog',
            name='was_connected_to',
        ),
    ]