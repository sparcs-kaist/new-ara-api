# LLM 식단 파서. 실패하면 크롤러가 정규식 파서로 넘어간다

from typing import Dict, List, Tuple, Union

MenuItemType = List[Union[str, List[int]]]
CourseDataType = Dict[Tuple[str, int], List[MenuItemType]]


class MealLLMError(Exception):
    pass


def parse_menu_with_llm(restaurant_code: str, lines: List[str], time: int) -> CourseDataType:
    raise MealLLMError("meal LLM server is not available yet")
