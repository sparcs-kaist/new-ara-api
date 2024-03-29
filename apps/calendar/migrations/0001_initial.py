# Generated by Django 4.2.3 on 2024-01-03 07:17

import datetime

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Tag",
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
                    "ko_name",
                    models.CharField(max_length=255, unique=True, verbose_name="한글 이름"),
                ),
                (
                    "en_name",
                    models.CharField(max_length=255, unique=True, verbose_name="영어 이름"),
                ),
                (
                    "color",
                    models.CharField(
                        default="#000000", max_length=7, verbose_name="HEX 코드"
                    ),
                ),
            ],
            options={
                "verbose_name": "태그",
                "verbose_name_plural": "태그 목록",
            },
        ),
        migrations.CreateModel(
            name="Event",
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
                        default=datetime.datetime(
                            1, 1, 1, 0, 0, tzinfo=datetime.timezone.utc
                        ),
                        verbose_name="삭제 시간",
                    ),
                ),
                (
                    "is_all_day",
                    models.BooleanField(default=False, verbose_name="하루 종일"),
                ),
                ("start_at", models.DateTimeField(verbose_name="시작 시각")),
                ("end_at", models.DateTimeField(verbose_name="종료 시각")),
                ("ko_title", models.CharField(max_length=512, verbose_name="한글 제목")),
                ("en_title", models.CharField(max_length=512, verbose_name="영어 제목")),
                (
                    "ko_description",
                    models.TextField(
                        blank=True, max_length=512, null=True, verbose_name="한글 설명"
                    ),
                ),
                (
                    "en_description",
                    models.TextField(
                        blank=True, max_length=512, null=True, verbose_name="영어 설명"
                    ),
                ),
                (
                    "location",
                    models.CharField(
                        blank=True, max_length=512, null=True, verbose_name="장소"
                    ),
                ),
                ("url", models.URLField(blank=True, null=True, verbose_name="URL")),
                (
                    "tags",
                    models.ManyToManyField(
                        blank=True, to="calendar.tag", verbose_name="태그"
                    ),
                ),
            ],
            options={
                "verbose_name": "일정",
                "verbose_name_plural": "일정 목록",
                "ordering": ("-created_at",),
                "abstract": False,
            },
        ),
    ]
