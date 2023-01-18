# Generated by Django 3.2.16 on 2023-01-18 14:20

import datetime
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import utc
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0043_board_comment_access_mask'),
    ]

    operations = [
        migrations.CreateModel(
            name='PortalViewCount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now, verbose_name='생성 시간')),
                ('updated_at', models.DateTimeField(auto_now=True, db_index=True, verbose_name='수정 시간')),
                ('deleted_at', models.DateTimeField(db_index=True, default=datetime.datetime(1, 1, 1, 0, 0, tzinfo=utc), verbose_name='삭제 시간')),
                ('view_count', models.IntegerField(default=0, verbose_name='조회수 값')),
                ('article', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='게시물', to='core.article')),
            ],
            options={
                'verbose_name': '포탈 조회 기록',
                'ordering': ('-created_at',),
                'abstract': False,
            },
        ),
    ]
