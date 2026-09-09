"""학과게시판 접근 권한 체크 헬퍼.

course.access 와 같은 구조. 두 종류의 헬퍼:

- `can_*` : 원래 board mask 검사를 하던 곳에서 학과글일 때 same-major
  검사로 대체. (Article vote_*, Comment create 등)
- `deny_non_same_major_*` : 원래 mask 검사가 없던 곳 (Scrap/Report/Comment
  vote 등) 에 학과글일 때만 추가 검사를 끼움. 일반글은 동작 불변.

SSO 의 major 식별자는 `sso_user_info["kaist_v2_info"]` 안의
`std_dept_id` 이며, kaist_v2_info 는 JSON 문자열로 저장되어 있어 파싱이
필요하다. Major 모델의 PK(`std_dept_id`) 가 이 값(정수형)과 곧바로 일치한다.
"""

from __future__ import annotations

import json

from apps.core.models.board import BoardAccessPermissionType
from apps.major.constants import get_major_code


def is_major_article(article) -> bool:
    return article is not None and article.related_major_id is not None


def user_major_info(user) -> dict | None:
    """SSO `kaist_v2_info`를 major info dict로 parsing하며, 실패하면 `None`을 반환한다.
    Return shape: `std_dept_id`, `major_name`, `major_name_eng`."""
    profile = getattr(user, "profile", None)
    if profile is None:
        return None
    sso = profile.sso_user_info or {}
    raw = sso.get("kaist_v2_info")
    if not raw:
        return None
    try:
        # `JSONDecodeError`는 `ValueError` subclass이므로 별도로 처리하지 않는다.
        info = json.loads(raw) if isinstance(raw, str) else raw
    except (ValueError, TypeError):
        return None

    # Valid JSON이 항상 dict는 아니므로 type을 확인해 `.get()`의 `AttributeError`를 막는다.
    if not isinstance(info, dict):
        return None

    std_dept_id = info.get("std_dept_id")
    if std_dept_id is None:
        return None
    try:
        std_dept_id = int(std_dept_id)
    except (TypeError, ValueError):
        return None

    return {
        "std_dept_id": std_dept_id,
        "major_name": info.get("std_dept_kor_nm") or "",
        "major_name_eng": info.get("std_dept_eng_nm"),
    }


def user_major_id(user) -> int | None:
    """SSO의 `std_dept_id`를 `int`로 반환하며, 없거나 parsing에 실패하면 `None`을 반환한다."""
    info = user_major_info(user)
    return info["std_dept_id"] if info else None


def get_or_create_major_for_user(user):
    """User의 SSO info로 home `Major` row와 `UserMajor` relation을 lazy-create한다.
    SSO major info가 없으면 `None`을 반환한다."""
    from apps.major.models import Major, UserMajor

    info = user_major_info(user)
    if info is None:
        return None
    major, _ = Major.objects.get_or_create(
        std_dept_id=info["std_dept_id"],
        defaults={
            "major_name": info["major_name"],
            "major_name_eng": info["major_name_eng"],
            # SSO에 code가 없으므로 major name mapping을 사용한다.
            "major_code": get_major_code(info["major_name"]),
        },
    )
    # `UserMajor`는 home/favorite majors의 readable set이며 unique constraint로 idempotent하다.
    UserMajor.objects.get_or_create(user=user, major=major)
    return major


def _is_same_major(user, std_dept_id) -> bool:
    """User의 SSO `std_dept_id`와 target `Major` PK가 같은지 확인한다.
    `Major` row 존재 여부와 무관하게 SSO value만 비교한다."""
    user_dept_id = user_major_id(user)
    if user_dept_id is None:
        return False
    try:
        return int(std_dept_id) == user_dept_id
    except (TypeError, ValueError):
        return False


def user_added_major_ids(user) -> set[int]:
    """`UserMajor`에 저장된 home/favorite `Major` PK set을 반환한다."""
    from apps.major.models import UserMajor

    return set(UserMajor.objects.filter(user=user).values_list("major_id", flat=True))


def can_read_major(user, std_dept_id) -> bool:
    """User가 home major 또는 favorite major를 읽을 수 있는지 확인한다."""
    if _is_same_major(user, std_dept_id):
        return True
    try:
        std = int(std_dept_id)
    except (TypeError, ValueError):
        return False
    from apps.major.models import UserMajor

    return UserMajor.objects.filter(user=user, major_id=std).exists()


def can_read_major_article(user, article) -> bool:
    """Major article은 major read permission, 그 외에는 `read_access_mask`로 검사한다."""
    if is_major_article(article):
        return can_read_major(user, article.related_major_id)
    return article.parent_board.group_has_access_permission(
        BoardAccessPermissionType.READ, user.profile.group
    )


def can_comment_on_major_article(user, article) -> bool:
    """Major article은 same-major, 그 외에는 `comment_access_mask`로 검사한다."""
    if is_major_article(article):
        return _is_same_major(user, article.related_major_id)
    return article.parent_board.group_has_access_permission(
        BoardAccessPermissionType.COMMENT, user.profile.group
    )


def deny_non_same_major_access(user, article) -> bool:
    """다른 major의 article에 접근할 때만 `True`를 반환한다."""
    if not is_major_article(article):
        return False
    return not _is_same_major(user, article.related_major_id)


def _comment_parent_article(comment):
    parent = comment.parent_article
    if parent is None and comment.parent_comment is not None:
        parent = comment.parent_comment.parent_article
    return parent


def deny_non_same_major_comment_access(user, comment) -> bool:
    """다른 major article의 comment에 접근할 때만 `True`를 반환한다."""
    parent = _comment_parent_article(comment)
    if parent is None:
        return False
    return deny_non_same_major_access(user, parent)


def deny_unreadable_major_comment_access(user, comment) -> bool:
    """Major article의 comment에 read permission이 없으면 `True`를 반환한다.
    Home major와 `UserMajor`에 등록된 favorite major에는 read access를 허용한다."""
    parent = _comment_parent_article(comment)
    if not is_major_article(parent):
        return False
    return not can_read_major(user, parent.related_major_id)
