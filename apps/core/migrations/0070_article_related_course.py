import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0069_attachment_alias_alter_attachment_file"),
        ("course", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="article",
            name="related_course",
            field=models.ForeignKey(
                blank=True,
                default=None,
                help_text="과목별 게시판 글일 때 set. 일반 글은 null.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="article_set",
                to="course.course",
                verbose_name="관련 과목 게시판",
            ),
        ),
    ]
