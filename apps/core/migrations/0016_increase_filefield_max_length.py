# Generated by Django 3.1 on 2020-09-19 04:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_run_sql_for_full_index'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attachment',
            name='file',
            field=models.FileField(max_length=200, upload_to='files', verbose_name='링크'),
        ),
    ]