from django.db import models


class Major(models.Model):
    """학과 게시판

    major_id : 학과 id
    """
    major_id = models.PositiveIntegerField(
        verbose_name="major_id"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성 시간")

    class Meta:
        verbose_name = "학과 게시판"
        verbose_name_plural = "학과 게시판 목록"
        constraints = [
            models.UniqueConstraint(
                fields=["major_id"],
                name="major_unique_id",
            ),
        ]

    def __str__(self) -> str:
        return f"[{self.major_id}]"
