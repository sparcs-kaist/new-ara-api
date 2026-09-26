from unittest.mock import patch

from apps.core.management.scripts import meal_crawler
from apps.core.management.scripts.meal_llm import MealLLMError


def test_east_parser():
    lines = ["(한식)", "쌀밥", "김치콩나물국5,6,9", "총칼로리:1,215kcal", "(일품)", "카레라이스5,6,12"]
    assert meal_crawler._parser_east(lines, 1) == {
        ("한식", None): [["쌀밥", []], ["김치콩나물국", [5, 6, 9]]],
        ("일품", None): [["카레라이스", [5, 6, 12]]],
    }


def test_east_parser_without_header_and_closed():
    assert meal_crawler._parser_east(["쌀밥", "배추김치6,9"], 0) == {("조식", None): [["쌀밥", []], ["배추김치", [6, 9]]]}
    assert meal_crawler._parser_east(["운영없음"], 0) == {}


def test_header_with_notice_and_uppercase_kcal():
    lines = [
        "조식(3,500원) /*교직원 및 일반인에게는 과일,간식 제공이 제한됩니다.",
        "쌀밥",
        "(582Kcal)",
    ]
    assert meal_crawler._parser_fclt(lines, 0) == {("조식", 3500): [["쌀밥", []]]}


def test_bracket_course_name():
    assert meal_crawler._parse_course_header("[일품: 6,500원]") == ("일품", 6500)


def test_llm_first_then_regex():
    lines = ["(한식)", "쌀밥"]
    with patch.object(meal_crawler, "parse_menu_with_llm", return_value={("LLM", 0): [["밥", []]]}):
        assert meal_crawler._parse_meal("east1", lines, 1) == {("LLM", 0): [["밥", []]]}
    with patch.object(meal_crawler, "parse_menu_with_llm", side_effect=MealLLMError("down")):
        assert meal_crawler._parse_meal("east1", lines, 1) == {("한식", None): [["쌀밥", []]]}
