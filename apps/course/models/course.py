from django.db import models


class Course(models.Model):
    """과목 게시판 단위 = (course_code, year, semester, 교수 set).

    OTL 의 Lecture/Course 와 1:1 대응되지 않는다. "같은 코드 + 같은 학기 +
    같은 교수 집합" 인 분반을 합쳐 하나의 row 로 둔다 (다른 교수면 분리).
    OTL 의 데이터는 read-through cache 로만 사용하고 진실은 sync 결과로 갱신한다.
    """

    course_code = models.CharField(max_length=16, verbose_name="과목 코드")
    title = models.CharField(max_length=256, verbose_name="과목명")
    department_name = models.CharField(
        max_length=64, blank=True, default="", verbose_name="개설학과명"
    )
    year = models.PositiveSmallIntegerField(verbose_name="개설 연도")
    # OTL 표기: 1=봄, 2=여름, 3=가을, 4=겨울
    semester = models.PositiveSmallIntegerField(verbose_name="개설 학기")
    professors = models.ManyToManyField(
        "course.Professor",
        related_name="courses",
        verbose_name="담당 교수",
    )
    # 같은 (code, year, semester) 안에서 prof set 단위로 dedup 하기 위한 키.
    # 정렬된 professor.id 들을 "," 로 join 한 문자열.
    professors_key = models.CharField(max_length=128, verbose_name="교수 집합 키")
    credit = models.DecimalField(
        max_digits=4, decimal_places=1, null=True, blank=True, verbose_name="학점"
    )
    otl_course_id = models.PositiveIntegerField(
        verbose_name="OTL course.id (참조용)"
    )
    # 합체된 OTL Lecture id 들. trace 용 (디버깅/이후 lecture 단위 fetch 가 필요할 때).
    otl_lecture_ids = models.JSONField(
        default=list, verbose_name="합체된 OTL lecture.id 리스트"
    )
    last_synced_at = models.DateTimeField(auto_now=True, verbose_name="최근 동기화 시간")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성 시간")

    class Meta:
        verbose_name = "과목 게시판"
        verbose_name_plural = "과목 게시판 목록"
        constraints = [
            models.UniqueConstraint(
                fields=["course_code", "year", "semester", "professors_key"],
                name="course_unique_code_term_profs",
            ),
        ]
        indexes = [
            # /api/courses/?year=&semester= (학기 필터 카탈로그 조회) 용
            models.Index(
                fields=["year", "semester"],
                name="course_year_semester_idx",
            ),
            # 과목 코드 직검색 용 (내부 도구/디버깅)
            models.Index(fields=["course_code"], name="course_code_idx"),
        ]

    def __str__(self) -> str:
        return f"[{self.course_code}] {self.title} ({self.year}-{self.semester})"
