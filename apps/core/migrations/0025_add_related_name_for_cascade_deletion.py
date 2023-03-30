# Generated by Django 3.1 on 2020-10-30 13:51

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("core", "0024_article_comment_count"),
    ]

    operations = [
        migrations.AlterField(
            model_name="comment",
            name="attachment",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="comment_set",
                to="core.attachment",
                verbose_name="첨부 파일",
            ),
        ),
        migrations.AlterField(
            model_name="report",
            name="reported_by",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="report_set",
                to=settings.AUTH_USER_MODEL,
                verbose_name="신고자",
            ),
        ),
        migrations.AlterField(
            model_name="vote",
            name="voted_by",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="vote_set",
                to=settings.AUTH_USER_MODEL,
                verbose_name="투표자",
            ),
        ),
    ]
