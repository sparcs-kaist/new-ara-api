import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("course", "0004_backfill_course_groups"),
    ]

    operations = [
        migrations.AlterField(
            model_name="course",
            name="group",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="courses",
                to="course.coursegroup",
                verbose_name="과목 그룹",
            ),
        ),
    ]