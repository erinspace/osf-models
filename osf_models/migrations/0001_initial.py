# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-03-25 23:04
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import osf_models.models.base
import osf_models.utils.datetime_aware_jsonfield


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BlackListGuid',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('guid', models.CharField(db_index=True, max_length=255, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('data', osf_models.utils.datetime_aware_jsonfield.DatetimeAwareJSONField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Guid',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('guid', models.CharField(db_index=True, default=osf_models.models.base.generate_guid, max_length=255, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Node',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('data', osf_models.utils.datetime_aware_jsonfield.DatetimeAwareJSONField()),
                ('guid', models.OneToOneField(default=osf_models.models.base.generate_guid_instance, on_delete=django.db.models.deletion.CASCADE, related_name='referent_node', to='osf_models.Guid')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('data', osf_models.utils.datetime_aware_jsonfield.DatetimeAwareJSONField()),
                ('guid', models.OneToOneField(default=osf_models.models.base.generate_guid_instance, on_delete=django.db.models.deletion.CASCADE, related_name='referent_user', to='osf_models.Guid')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='comment',
            name='guid',
            field=models.OneToOneField(default=osf_models.models.base.generate_guid_instance, on_delete=django.db.models.deletion.CASCADE, related_name='referent_comment', to='osf_models.Guid'),
        ),
    ]