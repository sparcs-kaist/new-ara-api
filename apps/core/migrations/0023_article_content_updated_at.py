# Generated by Django 3.1 on 2020-10-29 16:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0022_auto_20201009_0238"),
    ]

    operations = [
        migrations.AddField(
            model_name="article",
            name="content_updated_at",
            field=models.DateTimeField(
                default=None, null=True, verbose_name="제목/본문/첨부파일 수정 시간"
            ),
        ),
    ]
