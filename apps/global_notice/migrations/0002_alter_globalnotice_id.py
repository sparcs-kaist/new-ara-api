# Generated by Django 4.2.3 on 2024-01-05 07:51

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("global_notice", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="globalnotice",
            name="id",
            field=models.AutoField(
                auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
    ]
