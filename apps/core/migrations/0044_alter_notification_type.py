# Generated by Django 3.2.16 on 2023-01-23 07:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0043_board_comment_access_mask'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='type',
            field=models.CharField(choices=[('default', 'default'), ('article_commented', 'article_commented'), ('comment_commented', 'comment_commented'), ('article_new', 'article_new')], default='default', max_length=32, verbose_name='알림 종류'),
        ),
    ]
