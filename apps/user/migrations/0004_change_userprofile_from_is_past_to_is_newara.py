# Generated by Django 2.2.15 on 2020-08-20 01:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0003_created_at_to_auto_now_add'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='is_newara',
            field=models.BooleanField(default=True, verbose_name='뉴아라 사용자'),
        ),
        migrations.AlterUniqueTogether(
            name='userprofile',
            unique_together={('nickname', 'is_newara', 'deleted_at'), ('sid', 'deleted_at'), ('uid', 'deleted_at')},
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='is_past',
        ),
    ]
