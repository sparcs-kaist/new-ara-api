# Generated by Django 3.1 on 2020-09-21 14:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_add_migrated_fields_in_article'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='migrated_negative_vote_count',
            field=models.IntegerField(default=0, verbose_name='이전된 싫어요 수'),
        ),
    ]