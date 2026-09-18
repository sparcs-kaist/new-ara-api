from django.db import migrations


def backfill_course_group(apps, schema_editor):
    """기존 과목게시판 글의 related_course_group 을 해당 Course 의 group 으로 채운다."""
    Article = apps.get_model("core", "Article")
    articles = Article.objects.filter(
        related_course__isnull=False, related_course_group__isnull=True
    ).select_related("related_course")
    for article in articles.iterator():
        article.related_course_group_id = article.related_course.group_id
        article.save(update_fields=["related_course_group"])


def reverse(apps, schema_editor):
    Article = apps.get_model("core", "Article")
    Article.objects.update(related_course_group=None)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0072_article_related_course_group_and_more"),
    ]

    operations = [
        migrations.RunPython(backfill_course_group, reverse),
    ]