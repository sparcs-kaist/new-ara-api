# Generated by Django 2.2.15 on 2020-08-14 23:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_bestarticle_article_foreignkey'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bestarticle',
            name='best_by',
            field=models.CharField(choices=[('positive_vote_count', 'positive_vote_count')], default='positive_vote_count', max_length=32, verbose_name='베스트 문서 선정 기준'),
        ),
    ]
