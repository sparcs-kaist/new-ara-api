# Generated by Django 3.1 on 2020-10-08 17:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0021_board_is_hidden"),
    ]

    operations = [
        migrations.AlterField(
            model_name="article",
            name="url",
            field=models.TextField(
                blank=True, default=None, null=True, verbose_name="링크"
            ),
        ),
    ]
