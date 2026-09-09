"""학과 관련 상수.

SSO(kaist_v2_info)는 학과 이름(std_dept_kor_nm)만 주고 학과 코드는 주지 않는다.
Major row 를 lazy 생성할 때(apps.major.access.get_or_create_major_for_user) 이
표를 참조해 major_code 를 채운다.
"""

from __future__ import annotations

# 학과 이름(SSO std_dept_kor_nm) → 학과 코드.
# 표에 없는 학과는 code 가 빈 문자열로 남는다 (표에 항목을 추가하면 됨).
MAJOR_CODE_BY_NAME: dict[str, str] = {
    "인문사회과학부": "HSS",  # 인문
    "건설및환경공학과": "CE",  # 건환
    "기술경영학부": "BTM",  # 기경
    "기계공학과": "ME",  # 기계
    "물리학과": "PH",  # 물리
    "바이오및뇌공학과": "BiS",  # 바공
    "산업및시스템공학과": "IE",  # 산공
    "산업디자인학과": "ID",  # 산디
    "생명과학과": "BS",  # 생명
    "수리과학과": "MAS",  # 수리
    "원자력및양자공학과": "NQE",  # 원양
    "전기및전자공학부": "EE",  # 전자
    "전산학부": "CS",  # 전산
    "항공우주공학과": "AE",  # 항공
    "화학과": "CH",  # 화학
    "생명화학공학과": "CBE",  # 생화공
    "신소재공학과": "MS",  # 신소재
    "융합인재학부": "TS",  # 융인
    "반도체시스템공학과": "SS",  # 반시공
    "뇌인지과학과": "BCS",  # 뇌인지
    "새내기과정학부": "FM",  # TODO: 코드 검증 필요
    # "기타": 특정 학과에 대응하지 않는 그룹이라 코드 매핑 제외
}


def get_major_code(major_name: str | None) -> str:
    """Major name에 대응하는 code를 반환하며, mapping이 없으면 빈 string을 반환한다."""
    if not major_name:
        return ""
    return MAJOR_CODE_BY_NAME.get(major_name.strip(), "")
