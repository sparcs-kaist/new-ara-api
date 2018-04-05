# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2018-04-05 15:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('session', '0003_auto_20180405_1547'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='created_at',
            field=models.DateTimeField(default=None, null=True, verbose_name='생성 시간'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='deleted_at',
            field=models.DateTimeField(default=None, null=True, verbose_name='삭제 시간'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='updated_at',
            field=models.DateTimeField(default=None, null=True, verbose_name='수정 시간'),
        ),
    ]
