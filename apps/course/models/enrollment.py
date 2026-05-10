from django.conf import settings
from django.db import models

from ara.db.models import MetaDataModel


class CourseEnrollment(MetaDataModel):
    """유저의 수강 이력. OTL sync 응답의 mirror.

    soft-delete (MetaDataModel) 사용:
    - 드랍 시 hard-delete 가 아니라 deleted_at 설정 → audit/복구 가능
    - 수강변경 기간에 드랍 → 재신청 시 default manager 가 active 로
      못 보니 새 row 가 생성. 옛날 row 는 그대로 남아 history 보존.
    - 본인이 작성한 Article/Comment 는 enrollment 와 별도 테이블이라
      enrollment 가 사라져도 영향 없음 (Article.related_course 는
      Course 에 FK; Course/Article cascade 룰만이 영향). 권한만 잠깐
      잃었다가 재신청 시 회복.
    - OTL 응답이 깨져 모든 enrollment 를 wipe 하는 사고 시에도 row
      자체는 보존되어 admin 복구 가능.
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

    class Meta(MetaDataModel.Meta):
        verbose_name = "수강 이력"
        verbose_name_plural = "수강 이력 목록"
        constraints = [
            # deleted_at 까지 포함해야 같은 (user, course) 의 soft-deleted row 와
            # 새 active row 가 unique 충돌 없이 공존할 수 있다 (재수강 케이스).
            models.UniqueConstraint(
                fields=["user", "course", "deleted_at"],
                name="enrollment_unique_user_course",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.user_id} ↔ {self.course_id}"
