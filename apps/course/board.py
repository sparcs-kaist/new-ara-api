"""과목게시판 글들의 부모 Board 헬퍼.

Article.parent_board 가 NOT NULL 이라 dummy "course-articles-internal" Board
하나를 만들고 모든 과목게시판 글이 이 board 를 parent_board 로 가진다.
이 board 는 hidden + access mask 0 으로 두어 일반 board 라우트로는 접근
불가하다. 실제 권한은 IsEnrolledInCourse 가 별도로 검사한다.
"""

from __future__ import annotations

import threading

_COURSES_BOARD_EN_NAME = "course-articles-internal"
_COURSES_BOARD_KO_NAME = "과목게시판(internal)"

_cached_board_id: int | None = None
_lock = threading.Lock()


def get_courses_board_id() -> int:
    """첫 호출 시 board 생성 + id 캐시. 이후엔 in-memory 반환."""
    global _cached_board_id
    if _cached_board_id is not None:
        return _cached_board_id

    with _lock:
        if _cached_board_id is not None:
            return _cached_board_id

        from apps.core.models import Board
        from apps.core.models.board import NameType

        board, _ = Board.objects.get_or_create(
            en_name=_COURSES_BOARD_EN_NAME,
            defaults={
                "ko_name": _COURSES_BOARD_KO_NAME,
                "is_hidden": True,
                "read_access_mask": 0,
                "write_access_mask": 0,
                "comment_access_mask": 0,
                "name_type": (NameType.REGULAR | NameType.ANONYMOUS).value,
            },
        )
        _cached_board_id = board.id
        return _cached_board_id
