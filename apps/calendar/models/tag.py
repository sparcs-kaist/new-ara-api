from django.contrib import admin
from django.db import models
from django.utils.html import format_html


class Tag(models.Model):
    ko_name = models.CharField(
        verbose_name="한글 이름",
        max_length=255,
        unique=True,
    )
    en_name = models.CharField(
        verbose_name="영어 이름",
        max_length=255,
        unique=True,
    )
    color = models.CharField(
        verbose_name="HEX 코드",
        max_length=7,
        default="#000000",
    )

    class Meta:
        verbose_name = "태그"
        verbose_name_plural = "태그 목록"

    def __str__(self) -> str:
        return self.ko_name

    @admin.display(description="한글 이름")
    def colored_ko_name(self):
        return format_html(
            "<span style='color: {}'>{}</span>",
            self.color,
            self.ko_name,
        )
