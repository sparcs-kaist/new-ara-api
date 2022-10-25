# Generated by Django 3.2 on 2021-09-02 11:42

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0015_fix_inactive_due_at_verbose_name"),
    ]

    operations = [
        migrations.AlterField(
            model_name="manualuser",
            name="created_at",
            field=models.DateTimeField(
                db_index=True, default=django.utils.timezone.now, verbose_name="생성 시간"
            ),
        ),
        migrations.AlterField(
            model_name="userprofile",
            name="created_at",
            field=models.DateTimeField(
                db_index=True, default=django.utils.timezone.now, verbose_name="생성 시간"
            ),
        ),
    ]
