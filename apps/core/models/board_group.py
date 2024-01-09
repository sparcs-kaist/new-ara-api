from django.db import models


class BoardGroup(models.Model):
    class Meta:
        verbose_name = "게시판 그룹"
        verbose_name_plural = "게시판 그룹 목록"

    ko_name = models.CharField(
        verbose_name="게시판 그룹 국문 이름",
        max_length=64,
    )
    en_name = models.CharField(
        verbose_name="게시판 그룹 영문 이름",
        max_length=64,
    )
    slug = models.SlugField(
        verbose_name="슬러그",
        max_length=32,
        unique=True,
    )

    def __str__(self) -> str:
        return self.ko_name
