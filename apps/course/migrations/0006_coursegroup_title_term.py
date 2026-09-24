"""CourseGroup 에 대표 title 의 출처 학기(title_year/title_semester) 기록.

기존 row 는 그룹에 속한 가장 최신 학기 Course 기준으로 채운다. 이 과정에서
과거 학기 sync 때문에 옛 이름으로 회귀해 있던 대표명도 함께 교정된다.
"""

from django.db import migrations, models


def backfill_title_term(apps, schema_editor):
    CourseGroup = apps.get_model("course", "CourseGroup")

    for group in CourseGroup.objects.all().iterator():
        latest = (
            group.courses.order_by("-year", "-semester").first()
        )
        if latest is None:
            # Course 가 하나도 안 달린 그룹(정상적으론 없음). title 은 그대로 두고
            # 출처만 비워 둔다 -> 다음 sync 가 (0, 0) 취급해 바로 갱신한다.
            continue
        group.title = latest.title
        group.title_year = latest.year
        group.title_semester = latest.semester
        group.save(update_fields=["title", "title_year", "title_semester"])


def reverse_noop(apps, schema_editor):
    # 컬럼 자체가 되돌려지므로 데이터 복원은 불필요.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("course", "0005_course_group_non_null"),
    ]

    operations = [
        migrations.AddField(
            model_name="coursegroup",
            name="title_year",
            field=models.PositiveSmallIntegerField(
                blank=True, null=True, verbose_name="대표 과목명 출처 연도"
            ),
        ),
        migrations.AddField(
            model_name="coursegroup",
            name="title_semester",
            field=models.PositiveSmallIntegerField(
                blank=True, null=True, verbose_name="대표 과목명 출처 학기"
            ),
        ),
        migrations.RunPython(backfill_title_term, reverse_noop),
    ]
