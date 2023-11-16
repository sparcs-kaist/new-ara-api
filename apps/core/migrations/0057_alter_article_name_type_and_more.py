# Generated by Django 4.2.3 on 2023-09-21 08:27

from django.db import migrations, models

import apps.core.models.board


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0056_alter_article_comment_count_alter_article_hit_count_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="article",
            name="name_type",
            field=models.PositiveSmallIntegerField(
                db_index=True,
                default=apps.core.models.board.NameType["REGULAR"],
                verbose_name="익명 혹은 실명 여부",
            ),
        ),
        migrations.AddIndex(
            model_name="article",
            index=models.Index(
                fields=["created_at", "parent_board_id"],
                name="created_at_parent_board_id_idx",
            ),
        ),
    ]