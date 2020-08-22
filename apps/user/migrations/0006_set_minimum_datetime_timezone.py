# Generated by Django 3.1 on 2020-08-21 16:12

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0005_auto_add_updated_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='deleted_at',
            field=models.DateTimeField(db_index=True, default=datetime.datetime(1, 1, 1, 0, 0, tzinfo=utc), verbose_name='삭제 시간'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='nickname_updated_at',
            field=models.DateTimeField(default=datetime.datetime(1, 1, 1, 0, 0, tzinfo=utc), verbose_name='최근 닉네임 변경일시'),
        ),
    ]
