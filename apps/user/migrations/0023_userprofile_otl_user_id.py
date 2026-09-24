from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0022_alter_manualuser_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="otl_user_id",
            field=models.PositiveIntegerField(
                blank=True,
                default=None,
                editable=False,
                help_text=(
                    "OTL /api/v2/users/info 에서 받은 numeric id. /lectures path "
                    "호출에 필요."
                ),
                null=True,
                verbose_name="OTL user.id (cache)",
            ),
        ),
    ]
