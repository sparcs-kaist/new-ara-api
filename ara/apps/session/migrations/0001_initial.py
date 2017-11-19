# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-11-19 21:19
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sid', models.CharField(max_length=30)),
                ('signature', models.TextField(verbose_name='서명')),
                ('see_sexual', models.BooleanField(default=False, verbose_name='성인/음란성 보기')),
                ('see_social', models.BooleanField(default=False, verbose_name='정치/사회성 보기')),
                ('user_nickname', models.CharField(max_length=128, verbose_name='닉네임')),
                ('profile_picture', models.ImageField(upload_to='', verbose_name='프로필')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='사용자')),
            ],
        ),
    ]
