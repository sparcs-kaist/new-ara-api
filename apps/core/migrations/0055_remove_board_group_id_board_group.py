# Generated by Django 4.2.3 on 2023-07-22 14:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0054_boardgroup"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="board",
            name="group_id",
        ),
        migrations.AddField(
            model_name="board",
            name="group",
            field=models.ForeignKey(
                default=None,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="boards",
                to="core.boardgroup",
                verbose_name="게시판 그룹",
            ),
        ),
    ]
