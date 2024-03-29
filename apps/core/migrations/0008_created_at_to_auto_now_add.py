# Generated by Django 2.2.15 on 2020-08-14 23:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0007_bestarticle_multiple_choice"),
    ]

    operations = [
        migrations.AlterField(
            model_name="article",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True, db_index=True, verbose_name="생성 시간"
            ),
        ),
        migrations.AlterField(
            model_name="articledeletelog",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True, db_index=True, verbose_name="생성 시간"
            ),
        ),
        migrations.AlterField(
            model_name="articlereadlog",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True, db_index=True, verbose_name="생성 시간"
            ),
        ),
        migrations.AlterField(
            model_name="articleupdatelog",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True, db_index=True, verbose_name="생성 시간"
            ),
        ),
        migrations.AlterField(
            model_name="attachment",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True, db_index=True, verbose_name="생성 시간"
            ),
        ),
        migrations.AlterField(
            model_name="bestarticle",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True, db_index=True, verbose_name="생성 시간"
            ),
        ),
        migrations.AlterField(
            model_name="bestcomment",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True, db_index=True, verbose_name="생성 시간"
            ),
        ),
        migrations.AlterField(
            model_name="block",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True, db_index=True, verbose_name="생성 시간"
            ),
        ),
        migrations.AlterField(
            model_name="board",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True, db_index=True, verbose_name="생성 시간"
            ),
        ),
        migrations.AlterField(
            model_name="comment",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True, db_index=True, verbose_name="생성 시간"
            ),
        ),
        migrations.AlterField(
            model_name="commentdeletelog",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True, db_index=True, verbose_name="생성 시간"
            ),
        ),
        migrations.AlterField(
            model_name="commentupdatelog",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True, db_index=True, verbose_name="생성 시간"
            ),
        ),
        migrations.AlterField(
            model_name="faq",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True, db_index=True, verbose_name="생성 시간"
            ),
        ),
        migrations.AlterField(
            model_name="notification",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True, db_index=True, verbose_name="생성 시간"
            ),
        ),
        migrations.AlterField(
            model_name="notificationreadlog",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True, db_index=True, verbose_name="생성 시간"
            ),
        ),
        migrations.AlterField(
            model_name="report",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True, db_index=True, verbose_name="생성 시간"
            ),
        ),
        migrations.AlterField(
            model_name="scrap",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True, db_index=True, verbose_name="생성 시간"
            ),
        ),
        migrations.AlterField(
            model_name="topic",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True, db_index=True, verbose_name="생성 시간"
            ),
        ),
        migrations.AlterField(
            model_name="vote",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True, db_index=True, verbose_name="생성 시간"
            ),
        ),
    ]
