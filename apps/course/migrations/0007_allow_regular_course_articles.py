from django.db import migrations

COURSE_BOARD_EN_NAME = "course-articles-internal"
ANONYMOUS = 2
REGULAR_AND_ANONYMOUS = 3


def allow_regular_course_articles(apps, schema_editor):
    Board = apps.get_model("core", "Board")
    Board.objects.filter(en_name=COURSE_BOARD_EN_NAME).update(
        name_type=REGULAR_AND_ANONYMOUS
    )


def restore_anonymous_only(apps, schema_editor):
    Board = apps.get_model("core", "Board")
    Board.objects.filter(
        en_name=COURSE_BOARD_EN_NAME,
        name_type=REGULAR_AND_ANONYMOUS,
    ).update(name_type=ANONYMOUS)


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0073_backfill_article_course_group"),
        ("course", "0006_coursegroup_title_term"),
    ]

    operations = [
        migrations.RunPython(
            allow_regular_course_articles,
            restore_anonymous_only,
        ),
    ]
