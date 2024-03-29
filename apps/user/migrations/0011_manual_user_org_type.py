# Generated by Django 3.1 on 2020-10-26 09:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0010_manualuser"),
    ]

    operations = [
        migrations.RenameField(
            model_name="manualuser",
            old_name="organization_name",
            new_name="org_name",
        ),
        migrations.AddField(
            model_name="manualuser",
            name="org_type",
            field=models.IntegerField(
                choices=[
                    (0, "Unauthorized user"),
                    (1, "KAIST member"),
                    (2, "Restaurant employee"),
                    (3, "Other employee"),
                ],
                default=0,
            ),
        ),
    ]
