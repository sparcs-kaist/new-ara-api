# Generated by Django 3.1 on 2020-10-01 14:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0020_bestsearch'),
    ]

    operations = [
        migrations.AddField(
            model_name='board',
            name='is_hidden',
            field=models.BooleanField(db_index=True, default=False, help_text='활성화했을 때 메인페이지 상단바 리스트에 나타나지 않습니다. (ex. 뉴아라공지)', verbose_name='리스트 숨김 게시판'),
        ),
    ]