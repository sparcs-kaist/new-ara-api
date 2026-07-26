from django.db import migrations


def backfill_groups(apps, schema_editor):
    """기존 Course 들을 (course_code, professors_key) 단위로 묶어 CourseGroup 생성·연결.

    대표 title 은 가장 최근 학기 Course 의 title 을 쓴다 (year, semester 내림차순 첫 row).

    멱등하게 작성한다. 중복 판정 근거를 프로세스 로컬 dict 가 아니라 DB 의
    unique 제약(coursegroup_unique_code_profs)에 두므로, 부분 적용 후 재실행이나
    sync 가 이미 만들어 둔 그룹이 있는 DB 에서도 안전하다.
    """
    Course = apps.get_model("course", "Course")
    CourseGroup = apps.get_model("course", "CourseGroup")

    for course in Course.objects.order_by("-year", "-semester").iterator():
        group, _ = CourseGroup.objects.get_or_create(
            course_code=course.course_code,
            professors_key=course.professors_key,
            # 정렬상 첫 등장 = 최신 학기 title. 이미 있으면 건드리지 않는다.
            defaults={"title": course.title},
        )
        if course.group_id != group.id:
            course.group_id = group.id
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