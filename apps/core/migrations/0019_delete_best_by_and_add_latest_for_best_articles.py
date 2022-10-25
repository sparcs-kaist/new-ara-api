# Generated by Django 3.1 on 2020-09-20 15:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0018_auto_20200921_2306"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="bestarticle",
            name="best_by",
        ),
        migrations.AddField(
            model_name="bestarticle",
            name="latest",
            field=models.BooleanField(
                db_index=True, default=True, verbose_name="최신 베스트 문서"
            ),
        ),
        migrations.AlterField(
            model_name="bestarticle",
            name="period",
            field=models.CharField(
                choices=[("daily", "daily"), ("weekly", "weekly")],
                db_index=True,
                default="daily",
                max_length=32,
                verbose_name="베스트 문서 종류",
            ),
        ),
    ]
