# Generated by Django 3.2.9 on 2022-03-28 11:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0038_communicationarticle'),
    ]

    operations = [
        migrations.AddField(
            model_name='board',
            name='is_school_communication',
            field=models.BooleanField(db_index=True, default=False, help_text='학교 소통 게시판 글임을 표시', verbose_name='학교와의 소통 게시판'),
        ),
    ]