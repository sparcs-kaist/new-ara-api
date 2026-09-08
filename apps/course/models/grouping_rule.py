from django.db import models


class CourseGroupingRule(models.Model):
    """관리자가 지정하는 과목별 누적 게시판 그룹 예외 규칙.

    규칙이 없거나 비활성화되어 있으면 기존 정책인 `(과목 코드, 교수 집합)`을
    사용한다. `COURSE_CODE` 전략은 담당 교수가 달라져도 과목 코드 하나를 같은
    누적 게시판으로 묶는다.
    """

    class Strategy(models.TextChoices):
        CODE_AND_PROFESSORS = (
            "CODE_AND_PROFESSORS",
            "과목 코드 + 교수 집합 (기본)",
        )
        COURSE_CODE = "COURSE_CODE", "과목 코드만 (교수 무시)"

    course_code = models.CharField(
        max_length=16,
        unique=True,
        verbose_name="과목 코드",
        help_text="예: MAS101. 대소문자와 앞뒤 공백은 저장 시 정규화됩니다.",
    )
    strategy = models.CharField(
        max_length=32,
        choices=Strategy.choices,
        default=Strategy.CODE_AND_PROFESSORS,
        verbose_name="그룹 정책",
    )
    is_active = models.BooleanField(default=True, verbose_name="활성화")
    description = models.TextField(
        blank=True,
        default="",
        verbose_name="적용 사유",
        help_text="예외 처리 이유와 관련 기획·운영 맥락을 기록합니다.",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성 시간")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정 시간")

    class Meta:
        verbose_name = "과목 그룹 예외 규칙"
        verbose_name_plural = "과목 그룹 예외 규칙 목록"
        ordering = ("course_code",)

    def save(self, *args, **kwargs):
        self.course_code = self.course_code.strip().upper()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"[{self.course_code}] {self.get_strategy_display()}"
