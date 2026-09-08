from django.conf import settings
from django.db import models


class Major(models.Model):
    """학과 게시판

    std_dept_id : SSO(kaist_v2_info) 의 std_dept_id. 학과 식별자이자 이 모델의 PK.
    URL /api/majors/<std_dept_id>/ 가 이 값을 그대로 사용하므로, 클라이언트는
    SSO 에서 받은 std_dept_id 를 별도 변환 없이 그대로 쓸 수 있다.

    row 는 사전 시드하지 않고, 유저가 자기 학과 게시판에 처음 접근할 때
    SSO 정보로 lazy get_or_create 된다 (apps.major.access 참고).
    """

    std_dept_id = models.PositiveIntegerField(
        primary_key=True,
        verbose_name="std_dept_id",
    )

    major_code = models.CharField(
        max_length=20, verbose_name="학과 코드", default="", blank=True
    )

    major_name = models.CharField(max_length=100, verbose_name="학과 이름", default="")
    major_name_eng = models.CharField(
        max_length=100, verbose_name="학과 이름(영문)", null=True
    )
    major_dept_location = models.CharField(
        max_length=100, verbose_name="학과 건물 위치", null=True
    )

    # 이 학과 게시판의 독자 집합. 사용자가 즐겨찾기한 타 학과뿐 아니라 최초
    # 접근 시 자동 등록되는 자기 SSO 학과도 through(UserMajor)에 포함된다.
    readers = models.ManyToManyField(
        to=settings.AUTH_USER_MODEL,
        through="major.UserMajor",
        related_name="added_majors",
        verbose_name="추가한 유저들",
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성 시간")

    class Meta:
        verbose_name = "학과 게시판"
        verbose_name_plural = "학과 게시판 목록"

    def __str__(self) -> str:
        return f"[{self.std_dept_id}] {self.major_name}"
