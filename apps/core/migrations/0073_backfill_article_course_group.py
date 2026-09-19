from django.db import migrations

CHUNK_SIZE = 20000

BACKFILL_SQL = """
UPDATE core_article a
JOIN course_course cc ON a.related_course_id = cc.id
SET a.related_course_group_id = cc.group_id
WHERE a.id >= %s AND a.id < %s
  AND a.related_course_id IS NOT NULL
  AND a.related_course_group_id IS NULL
"""


def backfill_course_group(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("SELECT MIN(id), MAX(id) FROM core_article")
        min_id, max_id = cursor.fetchone()
        if min_id is None:
            return
        for start in range(min_id, max_id + 1, CHUNK_SIZE):
            cursor.execute(BACKFILL_SQL, [start, start + CHUNK_SIZE])


def reverse(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            "UPDATE core_article SET related_course_group_id = NULL "
            "WHERE related_course_group_id IS NOT NULL"
        )


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("core", "0071_article_related_major"),
    ]

    operations = [
        migrations.RunPython(backfill_course_group, reverse),
    ]
