# Generated by Django 3.1 on 2020-10-24 16:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0008_run_sql_for_full_index'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='picture',
            field=models.ImageField(blank=True, default=None, null=True, upload_to='user_profiles/pictures', verbose_name='프로필'),
        ),
    ]