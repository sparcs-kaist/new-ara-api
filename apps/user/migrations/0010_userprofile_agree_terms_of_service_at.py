# Generated by Django 3.1 on 2020-10-26 14:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0009_auto_20201025_0136'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='agree_terms_of_service_at',
            field=models.DateTimeField(default=None, null=True, verbose_name='약관 동의 일시'),
        ),
    ]
