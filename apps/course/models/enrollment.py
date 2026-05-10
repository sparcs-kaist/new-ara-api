from django.conf import settings
from django.db import models


class CourseEnrollment(models.Model):
    """유저의 수강 이력. OTL sync 응답의 mirror — 응답에 없으면 hard delete 됨.

    OTL 이 끝난 학기의 takenLecture 도 계속 유지하므로 결과적으로 "들었던
    과목 게시판은 영구 보존" 이 자연스럽게 따라온다 (Ara 가 별도 보관 룰을
    가질 필요가 없다). 학기 중 드랍은 1일 sync cycle 안에 빠짐.
    """

    user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="course_enrollments",
        verbose_name="수강생",
    )
    course = models.ForeignKey(
        to="course.Course",
        on_delete=models.CASCADE,
        related_name="enrollments",
        verbose_name="과목",
    )
    last_seen_in_otl_at = models.DateTimeField(
        verbose_name="OTL 응답에서 마지막으로 본 시점"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="등록 시간")

    class Meta:
        verbose_name = "수강 이력"
        verbose_name_plural = "수강 이력 목록"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "course"],
                name="enrollment_unique_user_course",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.user_id} ↔ {self.course_id}"
