# Generated by Django 3.1 on 2020-08-20 18:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0004_change_userprofile_from_is_past_to_is_newara"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userprofile",
            name="updated_at",
            field=models.DateTimeField(
                auto_now=True, db_index=True, verbose_name="수정 시간"
            ),
        ),
    ]
