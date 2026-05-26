from django.db import migrations


def backfill_groups(apps, schema_editor):
    """기존 Course 들을 (course_code, professors_key) 단위로 묶어 CourseGroup 생성·연결.

    대표 title 은 가장 최근 학기 Course 의 title 을 쓴다 (year, semester 내림차순 첫 row).
    """
    Course = apps.get_model("course", "Course")
    CourseGroup = apps.get_model("course", "CourseGroup")

    seen: dict[tuple, int] = {}
    for course in Course.objects.order_by("-year", "-semester"):
        key = (course.course_code, course.professors_key)
        group_id = seen.get(key)
        if group_id is None:
            group = CourseGroup.objects.create(
                course_code=course.course_code,
                professors_key=course.professors_key,
                title=course.title,  # 정렬상 첫 등장 = 최신 학기 title
            )
            group_id = group.id
            seen[key] = group_id
        course.group_id = group_id
        course.save(update_fields=["group"])


def reverse(apps, schema_editor):
    Course = apps.get_model("course", "Course")
    CourseGroup = apps.get_model("course", "CourseGroup")
    Course.objects.update(group=None)
    CourseGroup.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("course", "0003_coursegroup_course_group"),
    ]

    operations = [
        migrations.RunPython(backfill_groups, reverse),
    ]