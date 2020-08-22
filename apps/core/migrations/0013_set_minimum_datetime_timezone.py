# Generated by Django 3.1 on 2020-08-21 16:12

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_auto_add_updated_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='deleted_at',
            field=models.DateTimeField(db_index=True, default=datetime.datetime(1, 1, 1, 0, 0, tzinfo=utc), verbose_name='삭제 시간'),
        ),
        migrations.AlterField(
            model_name='articledeletelog',
            name='deleted_at',
            field=models.DateTimeField(db_index=True, default=datetime.datetime(1, 1, 1, 0, 0, tzinfo=utc), verbose_name='삭제 시간'),
        ),
        migrations.AlterField(
            model_name='articlereadlog',
            name='deleted_at',
            field=models.DateTimeField(db_index=True, default=datetime.datetime(1, 1, 1, 0, 0, tzinfo=utc), verbose_name='삭제 시간'),
        ),
        migrations.AlterField(
            model_name='articleupdatelog',
            name='deleted_at',
            field=models.DateTimeField(db_index=True, default=datetime.datetime(1, 1, 1, 0, 0, tzinfo=utc), verbose_name='삭제 시간'),
        ),
        migrations.AlterField(
            model_name='attachment',
            name='deleted_at',
            field=models.DateTimeField(db_index=True, default=datetime.datetime(1, 1, 1, 0, 0, tzinfo=utc), verbose_name='삭제 시간'),
        ),
        migrations.AlterField(
            model_name='bestarticle',
            name='deleted_at',
            field=models.DateTimeField(db_index=True, default=datetime.datetime(1, 1, 1, 0, 0, tzinfo=utc), verbose_name='삭제 시간'),
        ),
        migrations.AlterField(
            model_name='bestcomment',
            name='deleted_at',
            field=models.DateTimeField(db_index=True, default=datetime.datetime(1, 1, 1, 0, 0, tzinfo=utc), verbose_name='삭제 시간'),
        ),
        migrations.AlterField(
            model_name='block',
            name='deleted_at',
            field=models.DateTimeField(db_index=True, default=datetime.datetime(1, 1, 1, 0, 0, tzinfo=utc), verbose_name='삭제 시간'),
        ),
        migrations.AlterField(
            model_name='board',
            name='deleted_at',
            field=models.DateTimeField(db_index=True, default=datetime.datetime(1, 1, 1, 0, 0, tzinfo=utc), verbose_name='삭제 시간'),
        ),
        migrations.AlterField(
            model_name='comment',
            name='deleted_at',
            field=models.DateTimeField(db_index=True, default=datetime.datetime(1, 1, 1, 0, 0, tzinfo=utc), verbose_name='삭제 시간'),
        ),
        migrations.AlterField(
            model_name='commentdeletelog',
            name='deleted_at',
            field=models.DateTimeField(db_index=True, default=datetime.datetime(1, 1, 1, 0, 0, tzinfo=utc), verbose_name='삭제 시간'),
        ),
        migrations.AlterField(
            model_name='commentupdatelog',
            name='deleted_at',
            field=models.DateTimeField(db_index=True, default=datetime.datetime(1, 1, 1, 0, 0, tzinfo=utc), verbose_name='삭제 시간'),
        ),
        migrations.AlterField(
            model_name='faq',
            name='deleted_at',
            field=models.DateTimeField(db_index=True, default=datetime.datetime(1, 1, 1, 0, 0, tzinfo=utc), verbose_name='삭제 시간'),
        ),
        migrations.AlterField(
            model_name='notification',
            name='deleted_at',
            field=models.DateTimeField(db_index=True, default=datetime.datetime(1, 1, 1, 0, 0, tzinfo=utc), verbose_name='삭제 시간'),
        ),
        migrations.AlterField(
            model_name='notificationreadlog',
            name='deleted_at',
            field=models.DateTimeField(db_index=True, default=datetime.datetime(1, 1, 1, 0, 0, tzinfo=utc), verbose_name='삭제 시간'),
        ),
        migrations.AlterField(
            model_name='report',
            name='deleted_at',
            field=models.DateTimeField(db_index=True, default=datetime.datetime(1, 1, 1, 0, 0, tzinfo=utc), verbose_name='삭제 시간'),
        ),
        migrations.AlterField(
            model_name='scrap',
            name='deleted_at',
            field=models.DateTimeField(db_index=True, default=datetime.datetime(1, 1, 1, 0, 0, tzinfo=utc), verbose_name='삭제 시간'),
        ),
        migrations.AlterField(
            model_name='topic',
            name='deleted_at',
            field=models.DateTimeField(db_index=True, default=datetime.datetime(1, 1, 1, 0, 0, tzinfo=utc), verbose_name='삭제 시간'),
        ),
        migrations.AlterField(
            model_name='vote',
            name='deleted_at',
            field=models.DateTimeField(db_index=True, default=datetime.datetime(1, 1, 1, 0, 0, tzinfo=utc), verbose_name='삭제 시간'),
        ),
    ]