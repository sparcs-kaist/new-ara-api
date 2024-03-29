# Generated by Django 3.2.9 on 2022-05-05 16:34

import datetime

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models

import apps.core.models.communication_article


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0038_rename_is_anonymous_to_name_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="board",
            name="is_school_communication",
            field=models.BooleanField(
                db_index=True,
                default=False,
                help_text="학교 소통 게시판 글임을 표시",
                verbose_name="학교와의 소통 게시판",
            ),
        ),
        migrations.CreateModel(
            name="CommunicationArticle",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True,
                        default=django.utils.timezone.now,
                        verbose_name="생성 시간",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True, db_index=True, verbose_name="수정 시간"
                    ),
                ),
                (
                    "deleted_at",
                    models.DateTimeField(
                        db_index=True,
                        default=datetime.datetime(1, 1, 1, 0, 0, tzinfo=datetime.timezone.utc),
                        verbose_name="삭제 시간",
                    ),
                ),
                (
                    "response_deadline",
                    models.DateTimeField(
                        default=datetime.datetime(1, 1, 1, 0, 0, tzinfo=datetime.timezone.utc),
                        verbose_name="답변 요청 기한",
                    ),
                ),
                (
                    "confirmed_by_school_at",
                    models.DateTimeField(
                        default=datetime.datetime(1, 1, 1, 0, 0, tzinfo=datetime.timezone.utc),
                        verbose_name="학교측 문의 확인 시각",
                    ),
                ),
                (
                    "answered_at",
                    models.DateTimeField(
                        default=datetime.datetime(1, 1, 1, 0, 0, tzinfo=datetime.timezone.utc),
                        verbose_name="학교측 답변을 받은 시각",
                    ),
                ),
                (
                    "school_response_status",
                    models.SmallIntegerField(
                        default=apps.core.models.communication_article.SchoolResponseStatus[
                            "BEFORE_UPVOTE_THRESHOLD"
                        ],
                        verbose_name="답변 진행 상황",
                    ),
                ),
                (
                    "article",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="communication_article",
                        to="core.article",
                        verbose_name="게시물",
                    ),
                ),
            ],
            options={
                "verbose_name": "소통 게시물",
                "verbose_name_plural": "소통 게시물 목록",
                "ordering": ("-created_at",),
                "abstract": False,
            },
        ),
    ]
