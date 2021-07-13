# Generated by Django 3.1 on 2021-05-31 14:04

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0028_add_report_counts'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='hidden_at',
            field=models.DateTimeField(default=datetime.datetime(1, 1, 1, 0, 0, tzinfo=utc), verbose_name='숨김 시간'),
        ),
        migrations.AlterField(
            model_name='comment',
            name='hidden_at',
            field=models.DateTimeField(default=datetime.datetime(1, 1, 1, 0, 0, tzinfo=utc), verbose_name='숨김 시간'),
        ),
    ]
