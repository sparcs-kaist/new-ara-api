# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2018-06-20 00:27
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_auto_20180619_2219'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='article',
            options={'ordering': ('-created_at',), 'verbose_name': '문서', 'verbose_name_plural': '문서 목록'},
        ),
        migrations.AlterModelOptions(
            name='articledeletelog',
            options={'ordering': ('-created_at',), 'verbose_name': '게시물 삭제 기록', 'verbose_name_plural': '게시물 삭제 기록 목록'},
        ),
        migrations.AlterModelOptions(
            name='articlereadlog',
            options={'ordering': ('-created_at',), 'verbose_name': '게시물 조회 기록', 'verbose_name_plural': '게시물 조회 기록 목록'},
        ),
        migrations.AlterModelOptions(
            name='articleupdatelog',
            options={'ordering': ('-created_at',), 'verbose_name': '게시물 변경 기록', 'verbose_name_plural': '게시물 변경 기록 목록'},
        ),
        migrations.AlterModelOptions(
            name='attachment',
            options={'ordering': ('-created_at',), 'verbose_name': '첨부파일', 'verbose_name_plural': '첨부파일 목록'},
        ),
        migrations.AlterModelOptions(
            name='bestarticle',
            options={'ordering': ('-created_at',), 'verbose_name': '베스트 문서', 'verbose_name_plural': '베스트 문서 목록'},
        ),
        migrations.AlterModelOptions(
            name='bestcomment',
            options={'ordering': ('-created_at',), 'verbose_name': '베스트 댓글', 'verbose_name_plural': '베스트 댓글 목록'},
        ),
        migrations.AlterModelOptions(
            name='block',
            options={'ordering': ('-created_at',), 'verbose_name': '차단', 'verbose_name_plural': '차단 목록'},
        ),
        migrations.AlterModelOptions(
            name='board',
            options={'ordering': ('-created_at',), 'verbose_name': '게시판', 'verbose_name_plural': '게시판 목록'},
        ),
        migrations.AlterModelOptions(
            name='comment',
            options={'ordering': ('-created_at',), 'verbose_name': '댓글', 'verbose_name_plural': '댓글 목록'},
        ),
        migrations.AlterModelOptions(
            name='commentdeletelog',
            options={'ordering': ('-created_at',), 'verbose_name': '댓글 삭제 기록', 'verbose_name_plural': '댓글 삭제 기록 목록'},
        ),
        migrations.AlterModelOptions(
            name='commentupdatelog',
            options={'ordering': ('-created_at',), 'verbose_name': '댓글 변경 기록', 'verbose_name_plural': '댓글 변경 기록 목록'},
        ),
        migrations.AlterModelOptions(
            name='notification',
            options={'ordering': ('-created_at',), 'verbose_name': '알림', 'verbose_name_plural': '알림 목록'},
        ),
        migrations.AlterModelOptions(
            name='notificationreadlog',
            options={'ordering': ('-created_at',), 'verbose_name': '알림 조회 기록', 'verbose_name_plural': '알림 조회 기록 목록'},
        ),
        migrations.AlterModelOptions(
            name='report',
            options={'ordering': ('-created_at',), 'verbose_name': '신고', 'verbose_name_plural': '신고 목록'},
        ),
        migrations.AlterModelOptions(
            name='scrap',
            options={'ordering': ('-created_at',), 'verbose_name': '스크랩', 'verbose_name_plural': '스크랩 목록'},
        ),
        migrations.AlterModelOptions(
            name='topic',
            options={'ordering': ('-created_at',), 'verbose_name': '말머리', 'verbose_name_plural': '말머리 목록'},
        ),
        migrations.AlterModelOptions(
            name='vote',
            options={'ordering': ('-created_at',), 'verbose_name': '투표', 'verbose_name_plural': '투표 목록'},
        ),
        migrations.AddField(
            model_name='bestcomment',
            name='best_by',
            field=models.CharField(choices=[('positive_vote_count', 'positive_vote_count'), ('hit_count', 'hit_count')], default='positive_vote_count', max_length=32, verbose_name='베스트 댓글 선정 기준'),
        ),
        migrations.AddField(
            model_name='bestcomment',
            name='period',
            field=models.CharField(choices=[('daily', 'daily'), ('weekly', 'weekly')], default='daily', max_length=32, verbose_name='베스트 댓글 종류'),
        ),
    ]
