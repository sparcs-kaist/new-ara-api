from django.db import models


class CourseGroup(models.Model):
    """학기/연도와 무관하게 '같은 수업'을 묶는 단위.

    그룹 키 = (course_code, professors_key). 즉 과목 코드와 교수 집합이
    같으면 다른 학기에 열려도 한 그룹으로 본다. Course 가 학기별 row 라면
    CourseGroup 은 그 Course 들을 누적해 모으는 상위 묶음이다.

    OTL sync 가 새 학기 Course 를 만들 때 get_or_create 로 연결한다.
    """

    course_code = models.CharField(max_length=16, verbose_name="과목 코드")
    professors_key = models.CharField(max_length=128, verbose_name="교수 집합 키")
    # 대표 제목 = "가장 최신 학기" Course 의 title.
    # title_year / title_semester 는 지금 title 이 어느 학기에서 온 값인지를
    # 기록한다. sync 는 이 값보다 뒤(최신) 학기를 만났을 때만 title 을 갱신한다.
    # 이게 없으면 과거 학기를 sync 하는 것만으로 대표명이 옛 이름으로 회귀한다.
    title = models.CharField(max_length=256, verbose_name="대표 과목명")
    title_year = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name="대표 과목명 출처 연도"
    )
    title_semester = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name="대표 과목명 출처 학기"
    )

    def title_term(self) -> tuple[int, int]:
        """title 출처 학기를 비교 가능한 튜플로. 미기록이면 (0, 0) 취급."""
        return (self.title_year or 0, self.title_semester or 0)

    class Meta:
        verbose_name = "과목 그룹"
        verbose_name_plural = "과목 그룹 목록"
        constraints = [
            models.UniqueConstraint(
                fields=["course_code", "professors_key"],
                name="coursegroup_unique_code_profs",
            ),
        ]

    def __str__(self) -> str:
        return f"[{self.course_code}] {self.title}"