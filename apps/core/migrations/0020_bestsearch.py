# Generated by Django 3.1 on 2020-10-01 13:33

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0019_delete_best_by_and_add_latest_for_best_articles'),
    ]

    operations = [
        migrations.CreateModel(
            name='BestSearch',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='생성 시간')),
                ('updated_at', models.DateTimeField(auto_now=True, db_index=True, verbose_name='수정 시간')),
                ('deleted_at', models.DateTimeField(db_index=True, default=datetime.datetime(1, 1, 1, 0, 0, tzinfo=utc), verbose_name='삭제 시간')),
                ('ko_word', models.CharField(max_length=32, verbose_name='검색어 국문')),
                ('en_word', models.CharField(max_length=32, verbose_name='검색어 영문')),
                ('registered_by', models.CharField(choices=[('auto', 'auto'), ('manual', 'manual')], default='manual', max_length=32, verbose_name='추천 검색어 등록 방법')),
                ('latest', models.BooleanField(db_index=True, default=True, verbose_name='최신 추천 검색어')),
            ],
            options={
                'verbose_name': '추천 검색어',
                'verbose_name_plural': '추천 검색어 목록',
                'ordering': ('-created_at',),
                'abstract': False,
            },
        ),
    ]