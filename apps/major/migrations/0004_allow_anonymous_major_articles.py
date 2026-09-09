from django.db import migrations

MAJOR_BOARD_EN_NAME = "major-articles-internal"
REGULAR = 1
REGULAR_AND_ANONYMOUS = 3


def allow_anonymous_major_articles(apps, schema_editor):
    Board = apps.get_model("core", "Board")
    Board.objects.filter(en_name=MAJOR_BOARD_EN_NAME).update(
        name_type=REGULAR_AND_ANONYMOUS
    )


def restore_regular_only(apps, schema_editor):
    Board = apps.get_model("core", "Board")
    Board.objects.filter(
        en_name=MAJOR_BOARD_EN_NAME,
        name_type=REGULAR_AND_ANONYMOUS,
    ).update(name_type=REGULAR)


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0073_backfill_article_course_group"),
        ("major", "0003_major_major_code"),
    ]

    operations = [
        migrations.RunPython(
            allow_anonymous_major_articles,
            restore_regular_only,
        ),
    ]
