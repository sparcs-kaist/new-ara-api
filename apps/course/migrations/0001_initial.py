import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Professor",
            fields=[
                (
                    "id",
                    models.IntegerField(
                        primary_key=True, serialize=False, verbose_name="OTL professor id"
                    ),
                ),
                ("name", models.CharField(max_length=64, verbose_name="이름")),
                (
                    "last_synced_at",
                    models.DateTimeField(auto_now=True, verbose_name="최근 동기화 시간"),
                ),
            ],
            options={
                "verbose_name": "교수",
                "verbose_name_plural": "교수 목록",
            },
        ),
        migrations.CreateModel(
            name="Course",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "course_code",
                    models.CharField(max_length=16, verbose_name="과목 코드"),
                ),
                ("title", models.CharField(max_length=256, verbose_name="과목명")),
                (
                    "department_name",
                    models.CharField(
                        blank=True, default="", max_length=64, verbose_name="개설학과명"
                    ),
                ),
                ("year", models.PositiveSmallIntegerField(verbose_name="개설 연도")),
                (
                    "semester",
                    models.PositiveSmallIntegerField(verbose_name="개설 학기"),
                ),
                (
                    "professors_key",
                    models.CharField(max_length=128, verbose_name="교수 집합 키"),
                ),
                (
                    "credit",
                    models.DecimalField(
                        blank=True,
                        decimal_places=1,
                        max_digits=4,
                        null=True,
                        verbose_name="학점",
                    ),
                ),
                (
                    "otl_course_id",
                    models.PositiveIntegerField(verbose_name="OTL course.id (참조용)"),
                ),
                (
                    "otl_lecture_ids",
                    models.JSONField(
                        default=list, verbose_name="합체된 OTL lecture.id 리스트"
                    ),
                ),
                (
                    "last_synced_at",
                    models.DateTimeField(auto_now=True, verbose_name="최근 동기화 시간"),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="생성 시간"),
                ),
                (
                    "professors",
                    models.ManyToManyField(
                        related_name="courses",
                        to="course.professor",
                        verbose_name="담당 교수",
                    ),
                ),
            ],
            options={
                "verbose_name": "과목 게시판",
                "verbose_name_plural": "과목 게시판 목록",
            },
        ),
        migrations.CreateModel(
            name="CourseEnrollment",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "last_seen_in_otl_at",
                    models.DateTimeField(verbose_name="OTL 응답에서 마지막으로 본 시점"),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="등록 시간"),
                ),
                (
                    "course",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="enrollments",
                        to="course.course",
                        verbose_name="과목",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="course_enrollments",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="수강생",
                    ),
                ),
            ],
            options={
                "verbose_name": "수강 이력",
                "verbose_name_plural": "수강 이력 목록",
            },
        ),
        migrations.AddConstraint(
            model_name="course",
            constraint=models.UniqueConstraint(
                fields=("course_code", "year", "semester", "professors_key"),
                name="course_unique_code_term_profs",
            ),
        ),
        migrations.AddIndex(
            model_name="course",
            index=models.Index(
                fields=["year", "semester"], name="course_year_semester_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="course",
            index=models.Index(fields=["course_code"], name="course_code_idx"),
        ),
        migrations.AddConstraint(
            model_name="courseenrollment",
            constraint=models.UniqueConstraint(
                fields=("user", "course"), name="enrollment_unique_user_course"
            ),
        ),
    ]
