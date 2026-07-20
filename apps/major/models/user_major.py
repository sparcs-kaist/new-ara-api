from django.conf import settings
from django.db import models


class UserMajor(models.Model):
    """유저가 '추가(add)'한 타 학과 게시판 매핑 (독립 through 테이블).

    유저는 자기 SSO 학과 외에도, 여기 추가한 학과 게시판을 '읽기 전용'으로
    볼 수 있다. 쓰기(글/댓글/투표/스크랩/신고)는 여전히 자기 SSO 학과에서만
    가능하다. 자기 SSO 학과는 add 없이도 항상 접근되므로 이 테이블엔 담기지
    않고, '추가로 고른 타 학과'만 들어간다.

    단순 유저 선호 토글이라 soft-delete 를 쓰지 않는다 (remove = hard delete).
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
