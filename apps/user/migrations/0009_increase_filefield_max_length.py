# Generated by Django 3.1 on 2020-09-19 04:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0008_run_sql_for_full_index'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='group',
            field=models.IntegerField(choices=[(0, '미인증된 사용자'), (1, '카이스트 구성원'), (2, '식당 직원'), (3, '기타 직원')], default=0),
        ),
    ]