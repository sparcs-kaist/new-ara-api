# Generated by Django 3.1 on 2020-08-20 18:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_add_unique_together_in_block'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, db_index=True, verbose_name='수정 시간'),
        ),
        migrations.AlterField(
            model_name='articledeletelog',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, db_index=True, verbose_name='수정 시간'),
        ),
        migrations.AlterField(
            model_name='articlereadlog',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, db_index=True, verbose_name='수정 시간'),
        ),
        migrations.AlterField(
            model_name='articleupdatelog',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, db_index=True, verbose_name='수정 시간'),
        ),
        migrations.AlterField(
            model_name='attachment',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, db_index=True, verbose_name='수정 시간'),
        ),
        migrations.AlterField(
            model_name='bestarticle',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, db_index=True, verbose_name='수정 시간'),
        ),
        migrations.AlterField(
            model_name='bestcomment',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, db_index=True, verbose_name='수정 시간'),
        ),
        migrations.AlterField(
            model_name='block',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, db_index=True, verbose_name='수정 시간'),
        ),
        migrations.AlterField(
            model_name='board',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, db_index=True, verbose_name='수정 시간'),
        ),
        migrations.AlterField(
            model_name='comment',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, db_index=True, verbose_name='수정 시간'),
        ),
        migrations.AlterField(
            model_name='commentdeletelog',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, db_index=True, verbose_name='수정 시간'),
        ),
        migrations.AlterField(
            model_name='commentupdatelog',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, db_index=True, verbose_name='수정 시간'),
        ),
        migrations.AlterField(
            model_name='faq',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, db_index=True, verbose_name='수정 시간'),
        ),
        migrations.AlterField(
            model_name='notification',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, db_index=True, verbose_name='수정 시간'),
        ),
        migrations.AlterField(
            model_name='notificationreadlog',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, db_index=True, verbose_name='수정 시간'),
        ),
        migrations.AlterField(
            model_name='report',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, db_index=True, verbose_name='수정 시간'),
        ),
        migrations.AlterField(
            model_name='scrap',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, db_index=True, verbose_name='수정 시간'),
        ),
        migrations.AlterField(
            model_name='topic',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, db_index=True, verbose_name='수정 시간'),
        ),
        migrations.AlterField(
            model_name='vote',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, db_index=True, verbose_name='수정 시간'),
        ),
    ]