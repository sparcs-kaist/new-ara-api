# Generated by Django 2.2.15 on 2020-08-15 02:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_created_at_to_auto_now_add'),
    ]

    operations = [
        migrations.AddField(
            model_name='board',
            name='is_kaist',
            field=models.BooleanField(default=False, verbose_name='카이스트 구성원 전용 게시판'),
        ),
        migrations.AddField(
            model_name='board',
            name='is_readonly',
            field=models.BooleanField(default=False, help_text='활성화했을 때 관리자만 글을 쓸 수 있습니다. (ex. 포탈공지)', verbose_name='읽기 전용 게시판'),
        ),
    ]