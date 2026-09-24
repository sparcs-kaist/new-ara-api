from django.db import models


class Professor(models.Model):
    """OTL 의 Professor 미러. id 는 OTL professor.id 를 그대로 PK 로 사용."""

    id = models.IntegerField(primary_key=True, verbose_name="OTL professor id")
    name = models.CharField(max_length=64, verbose_name="이름")
    last_synced_at = models.DateTimeField(auto_now=True, verbose_name="최근 동기화 시간")

    class Meta:
        verbose_name = "교수"
        verbose_name_plural = "교수 목록"

    def __str__(self) -> str:
        return self.name
