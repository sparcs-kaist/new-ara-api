"""KAIST 식당 메뉴 크롤러.

식당 별 prefix
1. 카이마루       : fclt
2. 서맛골         : west
3. 교수회관       : emp

example URL: https://www.kaist.ac.kr/kr/html/campus/053001.html?dvs_cd=emp&stt_dt=2025-03-18

NOTE: 학교 홈페이지에 잡다한 안내(과일/이벤트/공지)가 메뉴 표 안에 섞여서
끊임없이 추가된다. 파서는 화이트리스트 방식(코스 헤더가 등장한 이후의 라인만
메뉴로 인정) + 광범위한 noise 키워드 필터로 견고성을 확보한다.
"""

import json
import logging
import re
from datetime import datetime, date as date_type
from typing import Callable, Dict, List, Optional, Tuple, Union

import requests
from bs4 import BeautifulSoup
from django.db import transaction

from apps.meal.models import Course, MealType, Menu, MenuAllergy, Restaurant


logger = logging.getLogger(__name__)


# ---------- 타입 ----------

# [메뉴명, [알러지코드들]] (e.g. ["김치찌개", [1, 5, 6]])
MenuItemType = List[Union[str, List[int]]]

# {(코스명, 가격): [메뉴아이템들]}
CourseDataType = Dict[Tuple[str, int], List[MenuItemType]]


# ---------- 상수 ----------

COMMON_URL = "https://www.kaist.ac.kr/kr/html/campus/053001.html?dvs_cd="

# 식당 코드 -> DB 식당명
RESTAURANT_CODE_TO_NAME = {
    "fclt": "카이마루",
    "west": "서맛골",
    "emp":  "교수회관",
}

TIME_INDEX_TO_MEAL_TYPE = {
    0: MealType.BREAKFAST,
    1: MealType.LUNCH,
    2: MealType.DINNER,
}

REQUEST_TIMEOUT = (5, 30)  # (connect, read)

# 메뉴 표 안에 섞여 들어오는 안내문 키워드. 이 키워드가 포함된 줄은 모두 무시한다.
# 학교 측에서 새로운 안내가 추가되면 여기에 추가하면 됨.
NOISE_KEYWORDS = (
    # 과일/식품 안내
    "하루과일", "과일",
    # 글로벌 행사 안내
    "글로벌",
    # 카이마루/교수회관 수요일 저녁 고객경영팀 하루과일 제공 안내
    "고객경영팀",
    # 서맛골 식사시 학생증 소지 안내
    "학생증",
    # 이벤트/행사 안내 (예: 초복, 벚꽃 팝콘)
    "이벤트", "event", "행사",
    # 칼로리 정보
    "kcal",
    # 공지/안내 일반
    "안내", "공지",
    # 모든 끼니 마지막에 항상 붙는 공통 샐러드 마커 - 메뉴로 취급하지 않는다.
    # 다른 메뉴(예: 치즈 샐러드)와 충돌을 피하기 위해 boilerplate 의 '드레싱' 부분을 키로 사용.
    "드레싱",
)

# 라인이 이 마커를 포함하면 그 시점부터 파싱 중단(식당 미운영 등).
END_MARKERS = ("미운영", "휴무")


# ---------- 정규식 ----------

# 코스 헤더: "이름(5,500원)", "이름[5,000원]", "<이름 5,500원>" 모두 허용.
# group 1 = 코스명, group 2 = 가격(쉼표 포함 가능).
_COURSE_HEADER_RX = re.compile(
    r"^<?\s*(.+?)\s*[\(\[\s]\s*([\d,]+)\s*원\s*[\)\]>]?\s*$"
)
# 메뉴 + 알러지 (괄호 표기): "김치찌개(1,2,5)"
_MENU_PAREN_RX = re.compile(r"^(.+?)\(([\d,\s]*)\)\s*$")
# 메뉴 + 알러지 (점 표기, 서맛골): "김치찌개 1.2.5", "김치찌개 1" 도 허용
_MENU_DOT_RX = re.compile(r"^(.+?)\s*(\d+(?:\.\d+)*)\s*$")


# ---------- 공통 유틸 ----------

def _parse_date(date_str: str) -> date_type:
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def current_date() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _is_noise(text: str) -> bool:
    return any(kw in text for kw in NOISE_KEYWORDS)


def _is_end_marker(text: str) -> bool:
    return any(marker in text for marker in END_MARKERS)


def _clean_lines(menu_list: List[str]) -> List[str]:
    """strip + 빈 줄 제거 + noise 라인 제거."""
    cleaned = []
    for raw in menu_list:
        s = raw.strip()
        if not s:
            continue
        if _is_noise(s):
            continue
        cleaned.append(s)
    return cleaned


def _parse_course_header(text: str) -> Optional[Tuple[str, int]]:
    """라인을 코스 헤더로 해석. 가격이 없으면 None."""
    if "원" not in text:
        return None
    m = _COURSE_HEADER_RX.match(text)
    if not m:
        return None
    name = m.group(1).strip().strip("<>").strip()
    if not name:
        return None
    try:
        price = int(m.group(2).replace(",", ""))
    except ValueError:
        return None
    return (name, price)


def _parse_menu_paren(text: str) -> MenuItemType:
    """'김치찌개(1,2,5)' 형식의 메뉴 라인을 파싱."""
    m = _MENU_PAREN_RX.match(text)
    if not m:
        return [text, []]
    name = m.group(1).strip()
    raw = m.group(2).strip()
    if not raw:
        return [name, []]
    try:
        allergens = [int(x.strip()) for x in raw.split(",") if x.strip()]
    except ValueError:
        return [name, []]
    return [name, allergens]


def _parse_menu_dot(text: str) -> MenuItemType:
    """'김치찌개 1.2.5' 형식 (서맛골) 의 메뉴 라인을 파싱."""
    m = _MENU_DOT_RX.match(text)
    if m:
        name = m.group(1).strip()
        try:
            allergens = [int(x) for x in m.group(2).split(".") if x]
        except ValueError:
            return [name, []]
        return [name, allergens]
    return [text, []]


def _merge_split_price_lines(items: List[str]) -> List[str]:
    """교수회관: 코스명 다음 줄에 가격 '(5,500원)' 이 따로 옴 -> 한 줄로 합침."""
    result: List[str] = []
    for raw in items:
        s = raw.strip()
        if not s:
            continue
        # 직전 라인이 코스 헤더가 아니고, 현재 라인이 가격 표기로만 이루어진 경우 합침
        if "원" in s and result and _parse_course_header(result[-1]) is None:
            result[-1] = result[-1] + s
        else:
            result.append(s)
    return result


# ---------- 식당별 파서 ----------

def _generic_course_parser(
    menu_list: List[str],
    parse_menu: Callable[[str], MenuItemType],
) -> CourseDataType:
    """
    표준 코스 파서.
    - 코스 헤더가 등장한 이후의 라인만 메뉴로 인정 (헤더 이전의 잡다한 라인은 무시).
    - 따라서 ('', 0) KeyError 가 발생하지 않는다.
    """
    cleaned = _clean_lines(menu_list)
    courses: CourseDataType = {}
    current: Optional[Tuple[str, int]] = None
    for line in cleaned:
        if _is_end_marker(line):
            break
        header = _parse_course_header(line)
        if header:
            current = header
            courses.setdefault(current, [])
            continue
        if current is None:
            logger.debug("meal_crawler: pre-header line skipped: %r", line)
            continue
        courses[current].append(parse_menu(line))
    return courses


def _parser_fclt(menu_list: List[str], time: int) -> CourseDataType:
    """카이마루: '코스명(5,500원)' / '메뉴(1,2,5)'"""
    return _generic_course_parser(menu_list, parse_menu=_parse_menu_paren)


def _parser_emp(menu_list: List[str], time: int) -> CourseDataType:
    """교수회관: 카이마루와 동일하나 '코스명' 과 '(5,500원)' 이 다른 라인에 들어옴."""
    merged = _merge_split_price_lines(menu_list)
    return _generic_course_parser(merged, parse_menu=_parse_menu_paren)


def _parser_west(menu_list: List[str], time: int) -> CourseDataType:
    """서맛골: 코스 헤더가 없을 수도 있고, 끼니별로 default 코스명/가격이 정해져 있다.
    - 조식 3,700원 / 중식 5,000원 / 석식 5,000원
    - 일품(별도 가격) 은 본문에 '[5,000원]' 형태로 등장
    - 메뉴 알러지 표기는 '김치찌개 1.2.5' 점 구분 형식
    - 조식 마지막 줄에 '천원의 아침밥' 이 붙으면 default 가 (천원의 아침밥, 1000) 로 바뀜
    """
    DEFAULT = {0: ("조식", 3700), 1: ("중식", 5000), 2: ("석식", 5000)}

    cleaned = _clean_lines(menu_list)
    if not cleaned:
        return {}
    if any(_is_end_marker(l) for l in cleaned[:1]):
        return {}

    default_course = DEFAULT.get(time, ("", 0))
    if time == 0 and "천원의 아침밥" in cleaned[-1]:
        default_course = ("천원의 아침밥", 1000)
        cleaned.pop()

    courses: CourseDataType = {default_course: []}
    current = default_course
    for line in cleaned:
        if _is_end_marker(line):
            break
        header = _parse_course_header(line)
        if header:
            current = header
            courses.setdefault(current, [])
            continue
        courses[current].append(_parse_menu_dot(line))

    if not courses[default_course]:
        del courses[default_course]
    return courses


_PARSERS: Dict[str, Callable[[List[str], int], CourseDataType]] = {
    "fclt": _parser_fclt,
    "west": _parser_west,
    "emp":  _parser_emp,
}


# ---------- 크롤링 ----------

def _crawl_meal(restaurant_code: str, date: str) -> Optional[List[CourseDataType]]:
    """식당 웹페이지에서 식단 정보를 크롤링.

    Returns:
        성공 시: [아침, 점심, 저녁] 코스 데이터 리스트
        실패 시: None
    """
    url = COMMON_URL + f"{restaurant_code}&stt_dt={date}"
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
    except requests.RequestException as e:
        logger.warning("[%s] HTTP 요청 실패: %s", restaurant_code, e)
        return None

    if response.status_code != 200:
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    parser = _PARSERS[restaurant_code]

    meal_info: List[CourseDataType] = []
    for nth in (1, 2, 3):
        cell = soup.select_one(
            f"#tab_item_1 > table > tbody > tr > td:nth-child({nth})"
        )
        if cell is None:
            return None
        text_lines = "".join(c.text for c in cell.contents).split("\r")
        meal_info.append(parser(text_lines, nth - 1))
    return meal_info


# ---------- DB 저장/비교 ----------

def _get_or_create_restaurant(restaurant_name: str) -> Restaurant:
    restaurant, _ = Restaurant.objects.get_or_create(restaurant_name=restaurant_name)
    return restaurant


def _get_existing_course_data(
    restaurant: Restaurant, date: date_type, meal_time: MealType
) -> CourseDataType:
    existing: CourseDataType = {}
    courses = Course.objects.filter(
        restaurant_id=restaurant,
        date=date,
        meal_time=meal_time.value,
    ).prefetch_related("menu_set__allergy_set")

    for course in courses:
        key = (course.course_name, course.price)
        menu_list: List[MenuItemType] = []
        for menu in course.menu_set.all():
            allergy_codes = [a.allergen_code for a in menu.allergy_set.all()]
            menu_list.append([menu.menu_name, allergy_codes])
        existing[key] = menu_list
    return existing


def _normalize_course_data(data: CourseDataType) -> str:
    if not data:
        return ""
    serializable = {
        f"{k[0]}_{k[1]}": sorted([str(v) for v in vals])
        for k, vals in sorted(data.items())
    }
    return json.dumps(serializable, sort_keys=True, ensure_ascii=False)


def _is_course_data_equal(a: CourseDataType, b: CourseDataType) -> bool:
    return _normalize_course_data(a) == _normalize_course_data(b)


def _save_course_to_db(
    restaurant: Restaurant,
    date: date_type,
    meal_time: MealType,
    course_data: CourseDataType,
) -> None:
    for (course_name, course_price), menu_list in course_data.items():
        course = Course.objects.create(
            restaurant_id=restaurant,
            course_name=course_name,
            price=course_price,
            date=date,
            meal_time=meal_time.value,
        )

        # MySQL bulk_create 는 PK 를 안 채워주므로 다시 조회해서 가져온다.
        Menu.objects.bulk_create(
            [Menu(menu_name=item[0], course_id=course) for item in menu_list]
        )
        created_menus = list(
            Menu.objects.filter(course_id=course).order_by("id")
        )

        allergies_to_create = []
        for menu_obj, item in zip(created_menus, menu_list):
            allergens = item[1] if len(item) > 1 else []
            for code in allergens:
                allergies_to_create.append(
                    MenuAllergy(allergen_code=code, menu_id=menu_obj)
                )
        if allergies_to_create:
            MenuAllergy.objects.bulk_create(allergies_to_create)


def _delete_course_by_meal_time(
    restaurant: Restaurant, date: date_type, meal_time: MealType
) -> None:
    Course.objects.filter(
        restaurant_id=restaurant, date=date, meal_time=meal_time.value
    ).delete()


# ---------- 식당 단위 처리 ----------

def _crawl_and_save_course_restaurant(restaurant_code: str, date_str: str) -> str:
    """
    한 식당의 코스 메뉴를 크롤링하고, 변경이 있을 때만 DB 업데이트.

    Returns: 'updated' | 'skipped' | 'failed'
    """
    db_restaurant_name = RESTAURANT_CODE_TO_NAME[restaurant_code]
    date = _parse_date(date_str)

    try:
        crawled = _crawl_meal(restaurant_code=restaurant_code, date=date_str)
        if crawled is None:
            logger.warning("[%s] 크롤링 실패 - HTTP 요청 실패", restaurant_code)
            return "failed"

        restaurant = _get_or_create_restaurant(db_restaurant_name)

        changes_needed = []
        for time_idx, new_data in enumerate(crawled):
            meal_type = TIME_INDEX_TO_MEAL_TYPE[time_idx]
            existing = _get_existing_course_data(restaurant, date, meal_type)

            if not new_data and not existing:
                continue
            if not _is_course_data_equal(existing, new_data or {}):
                changes_needed.append((time_idx, new_data, meal_type))

        if not changes_needed:
            logger.debug("[%s] 변경사항 없음 - 스킵", restaurant_code)
            return "skipped"

        with transaction.atomic():
            for time_idx, meal_data, meal_type in changes_needed:
                _delete_course_by_meal_time(restaurant, date, meal_type)
                if meal_data:
                    _save_course_to_db(restaurant, date, meal_type, meal_data)
                logger.info(
                    "[%s] %s 메뉴 업데이트됨", restaurant_code, meal_type.value
                )
        return "updated"

    except Exception as e:
        logger.error("[%s] 코스 메뉴 저장 실패: %s", restaurant_code, e)
        return "failed"


def crawl_daily_meal(date: str):
    """
    하루치 식단 크롤링 메인 함수.
    각 식당 별로 독립적으로 크롤링/저장하여 한 식당 실패가 다른 식당에 전파되지 않는다.
    DB 의 기존 데이터와 다른 경우에만 업데이트한다.
    """
    logger.info("=== 식단 크롤링 시작: %s ===", date)

    results = {"updated": [], "skipped": [], "failed": []}

    for code in RESTAURANT_CODE_TO_NAME:
        result = _crawl_and_save_course_restaurant(code, date)
        results[result].append(code)

    logger.info("=== 식단 크롤링 완료: %s ===", date)
    logger.info("업데이트: %s", results["updated"])
    logger.info("스킵 (변경없음): %s", results["skipped"])
    if results["failed"]:
        logger.warning("실패: %s", results["failed"])

    return results


if __name__ == "__main__":
    import os
    import django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ara.settings")
    django.setup()

    print("식단 크롤링 시작")
    res = crawl_daily_meal(date=current_date())
    print(f"결과: {res}")
