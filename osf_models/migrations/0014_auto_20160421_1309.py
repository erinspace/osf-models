# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-04-21 18:09
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('osf_models', '0013_auto_20160420_1956'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='contributor',
            unique_together=set([('user', 'node')]),
        ),
    ]