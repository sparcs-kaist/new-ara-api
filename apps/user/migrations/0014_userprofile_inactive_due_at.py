# Generated by Django 3.1 on 2021-02-03 11:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0013_userprofile_agree_terms_of_service_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='inactive_due_at',
            field=models.DateTimeField(default=None, null=True, verbose_name='약관 동의 일시'),
        ),
    ]