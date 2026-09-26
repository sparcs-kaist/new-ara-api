"""LLM 식단 파서.

qwen 등을 FastAPI 로 감싼 내부 서버가 올라오면 parse_menu_with_llm 에서 호출한다.
실패하면 크롤러가 정규식 파서로 넘어가므로, 여기서는 예외만 던지면 된다.
"""

from typing import Dict, List, Tuple, Union

MenuItemType = List[Union[str, List[int]]]
CourseDataType = Dict[Tuple[str, int], List[MenuItemType]]


class MealLLMError(Exception):
    pass


def parse_menu_with_llm(restaurant_code: str, lines: List[str], time: int) -> CourseDataType:
    raise MealLLMError("meal LLM server is not available yet")
