# Generated by Django 2.2.15 on 2020-08-19 02:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0009_board_perms"),
    ]

    operations = [
        migrations.AlterField(
            model_name="attachment",
            name="file",
            field=models.FileField(upload_to="files", verbose_name="링크"),
        ),
    ]
