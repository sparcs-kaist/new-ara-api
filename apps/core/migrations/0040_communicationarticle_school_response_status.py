# Generated by Django 3.2.9 on 2022-03-31 18:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0039_board_is_school_communication'),
    ]

    operations = [
        migrations.AddField(
            model_name='communicationarticle',
            name='school_response_status',
            field=models.SmallIntegerField(default=0, verbose_name='답변 진행 상황'),
        ),
    ]
