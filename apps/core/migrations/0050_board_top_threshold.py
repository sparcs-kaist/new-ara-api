# Generated by Django 3.2.16 on 2023-05-11 13:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0049_article_topped_at"),
    ]

    operations = [
        migrations.AddField(
            model_name="board",
            name="top_threshold",
            field=models.SmallIntegerField(default=10, verbose_name="인기글 달성 기준 좋아요 개수"),
        ),
    ]
