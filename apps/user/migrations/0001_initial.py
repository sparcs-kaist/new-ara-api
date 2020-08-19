# Generated by Django 2.2.15 on 2020-08-11 18:40

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django_mysql.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0011_update_proxy_permissions'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('created_at', models.DateTimeField(db_index=True, default=datetime.datetime(1, 1, 1, 0, 0), verbose_name='생성 시간')),
                ('updated_at', models.DateTimeField(default=datetime.datetime(1, 1, 1, 0, 0), verbose_name='수정 시간')),
                ('deleted_at', models.DateTimeField(db_index=True, default=datetime.datetime(1, 1, 1, 0, 0), verbose_name='삭제 시간')),
                ('uid', models.CharField(default=None, editable=False, max_length=30, null=True, verbose_name='Sparcs SSO uid')),
                ('sid', models.CharField(default=None, editable=False, max_length=30, null=True, verbose_name='Sparcs SSO sid')),
                ('sso_user_info', django_mysql.models.JSONField(default=dict, editable=False, verbose_name='Sparcs SSO 정보')),
                ('picture', models.ImageField(default=None, null=True, upload_to='user_profiles/pictures', verbose_name='프로필')),
                ('nickname', models.CharField(blank=True, default='', max_length=128, verbose_name='닉네임')),
                ('nickname_updated_at', models.DateTimeField(blank=True, default=None, null=True, verbose_name='최근 닉네임 변경일시')),
                ('see_sexual', models.BooleanField(default=False, verbose_name='성인/음란성 보기')),
                ('see_social', models.BooleanField(default=False, verbose_name='정치/사회성 보기')),
                ('extra_preferences', django_mysql.models.JSONField(default=dict, editable=False, verbose_name='기타 설정')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='profile', serialize=False, to=settings.AUTH_USER_MODEL, verbose_name='사용자')),
                ('past_user', models.BooleanField(default=False, verbose_name='이전 사용자')),
                ('ara_id', models.CharField(blank=True, default='', max_length=128, verbose_name='이전 아라 아이디')),
            ],
            options={
                'verbose_name': '유저 프로필',
                'verbose_name_plural': '유저 프로필 목록',
                'ordering': ('-created_at',),
                'abstract': False,
                'unique_together': {('sid', 'deleted_at'), ('uid', 'deleted_at'), ('nickname', 'past_user', 'deleted_at')},
            },
        ),
    ]
