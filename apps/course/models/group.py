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
    # 대표 제목. 가장 최근 sync 된 Course 의 title 로 갱신될 수 있다.
    title = models.CharField(max_length=256, verbose_name="대표 과목명")

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