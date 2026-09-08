from django.conf import settings
from django.db import models


class UserMajor(models.Model):
    """유저가 읽는 학과 게시판을 기록하는 독립 through 테이블.

    사용자 관점에서 add/remove 하는 타 학과 row 는 즐겨찾기다. 구현상으로는
    readers_count와 my-major 조회를 단순하게 유지하기 위해 자기 SSO 학과도 최초
    접근 시 자동으로 row를 만든다. 따라서 UserMajor row 자체만 보고 사용자가
    직접 고른 즐겨찾기인지 자동 등록된 홈 학과인지 구분하면 안 되며, 구분할 때는
    현재 SSO std_dept_id와 비교해야 한다.

    홈 학과와 즐겨찾기 학과 모두 읽기와 글·댓글 투표가 가능하다. 글·댓글 작성,
    수정·삭제, 스크랩·신고는 홈 학과에서만 가능하다. 즐겨찾기 제거는 hard delete
    이고, 홈 학과 row는 API에서 제거하지 못하게 막는다.
    """

    user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="major_additions",
        verbose_name="유저",
    )
    major = models.ForeignKey(
        to="major.Major",
        on_delete=models.CASCADE,
        related_name="user_additions",
        verbose_name="추가한 학과 게시판",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="추가 시간")

    class Meta:
        verbose_name = "학과 게시판 추가"
        verbose_name_plural = "학과 게시판 추가 목록"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "major"],
                name="usermajor_unique",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.user_id} → [{self.major_id}]"
