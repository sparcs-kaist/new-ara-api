# Generated by Django 3.1 on 2021-02-25 12:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0014_userprofile_inactive_due_at"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userprofile",
            name="inactive_due_at",
            field=models.DateTimeField(
                default=None, null=True, verbose_name="활동정지 마감 일시"
            ),
        ),
    ]
