from django.conf import settings
from django.db import models

# 학과 이름(SSO std_dept_kor_nm) → 학과 코드 매핑.
# SSO 는 코드를 주지 않으므로, Major row 를 lazy 생성할 때 이 표를 참조해 채운다.
# 표에 없는 학과는 code 가 빈 문자열로 남는다 (표에 항목을 추가하면 됨).
MAJOR_CODE_BY_NAME: dict[str, str] = {
    "인문사회과학부": "HSS",       # 인문
    "건설및환경공학과": "CE",       # 건환
    "기술경영학부": "BTM",         # 기경
    "기계공학과": "ME",            # 기계
    "물리학과": "PH",             # 물리
    "바이오및뇌공학과": "BiS",      # 바공
    "산업및시스템공학과": "IE",      # 산공
    "산업디자인학과": "ID",         # 산디
    "생명과학과": "BS",            # 생명
    "수리과학과": "MAS",           # 수리
    "원자력및양자공학과": "NQE",     # 원양
    "전기및전자공학부": "EE",       # 전자
    "전산학부": "CS",             # 전산
    "항공우주공학과": "AE",         # 항공
    "화학과": "CH",               # 화학
    "생명화학공학과": "CBE",        # 생화공
    "신소재공학과": "MS",          # 신소재
    "융합인재학부": "TS",          # 융인
    "반도체시스템공학과": "SS",      # 반시공
    "뇌인지과학과": "BCS",         # 뇌인지
    "새내기과정학부": "FM"        # 코드 검증 필요
    # "기타": 특정 학과에 대응하지 않는 그룹이라 코드 매핑 제외
}


def get_major_code(major_name: str | None) -> str:
    """학과 이름으로 코드를 찾는다. 모르는 학과면 빈 문자열."""
    if not major_name:
        return ""
    return MAJOR_CODE_BY_NAME.get(major_name.strip(), "")


class Major(models.Model):
    """학과 게시판

    std_dept_id : SSO(kaist_v2_info) 의 std_dept_id. 학과 식별자이자 이 모델의 PK.
    URL /api/majors/<std_dept_id>/ 가 이 값을 그대로 사용하므로, 클라이언트는
    SSO 에서 받은 std_dept_id 를 별도 변환 없이 그대로 쓸 수 있다.

    row 는 사전 시드하지 않고, 유저가 자기 학과 게시판에 처음 접근할 때
    SSO 정보로 lazy get_or_create 된다 (apps.major.access 참고).
    """

    std_dept_id = models.PositiveIntegerField(
        primary_key=True,
        verbose_name="std_dept_id",
    )

    major_code = models.CharField(max_length=20, verbose_name="학과 코드", default="", blank=True)

    major_name = models.CharField(max_length=100, verbose_name="학과 이름", default="")
    major_name_eng = models.CharField(max_length=100, verbose_name="학과 이름(영문)", null=True)
    major_dept_location = models.CharField(max_length=100, verbose_name="학과 건물 위치", null=True)

    # 이 학과 게시판을 '추가(add)'해서 읽는 유저들. 컬럼은 through(UserMajor)에.
    readers = models.ManyToManyField(
        to=settings.AUTH_USER_MODEL,
        through="major.UserMajor",
        related_name="added_majors",
        verbose_name="추가한 유저들",
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성 시간")

    class Meta:
        verbose_name = "학과 게시판"
        verbose_name_plural = "학과 게시판 목록"

    def __str__(self) -> str:
        return f"[{self.std_dept_id}] {self.major_name}"
