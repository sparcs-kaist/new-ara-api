"""학과게시판 접근 권한 체크 헬퍼.

course.access 와 같은 구조. 두 종류의 헬퍼:

- `can_*` : 원래 board mask 검사를 하던 곳에서 학과글일 때 same-major
  검사로 대체. (Article vote_*, Comment create 등)
- `deny_non_same_major_*` : 원래 mask 검사가 없던 곳 (Scrap/Report/Comment
  vote 등) 에 학과글일 때만 추가 검사를 끼움. 일반글은 동작 불변.

SSO 의 major 식별자는 `sso_user_info["kaist_v2_info"]` 안의
`std_dept_id` 이며, kaist_v2_info 는 JSON 문자열로 저장되어 있어 파싱이
필요하다. Major 모델의 `major_id` 가 이 값(정수형)과 매칭된다.
"""


from __future__ import annotations

import json

from apps.core.models.board import BoardAccessPermissionType


def is_major_article(article) -> bool:
    return article is not None and article.related_major_id is not None


def user_major_id(user) -> int | None:
    """SSO 의 std_dept_id 를 정수로 반환. 없거나 파싱 실패 시 None."""
    profile = getattr(user, "profile", None)
    if profile is None:
        return None
    sso = profile.sso_user_info or {}
    raw = sso.get("kaist_v2_info")
    if not raw:
        return None
    try:
        info = json.loads(raw) if isinstance(raw, str) else raw
        dept_id = info.get("std_dept_id")
        return int(dept_id) if dept_id is not None else None
    except (ValueError, TypeError, json.JSONDecodeError):
        return None


def _is_same_major(user, major_pk: int) -> bool:
    """user 가 해당 Major (PK) 와 같은 학과인가."""
    from apps.major.models import Major

    user_dept = user_major_id(user)
    if user_dept is None:
        return False
    return Major.objects.filter(pk=major_pk, major_id=user_dept).exists()


def can_read_article(user, article) -> bool:
    """학과글이면 same-major, 아니면 parent_board.read_access_mask."""
    if is_major_article(article):
        return _is_same_major(user, article.related_major_id)
    return article.parent_board.group_has_access_permission(
        BoardAccessPermissionType.READ, user.profile.group
    )


def can_comment_on_article(user, article) -> bool:
    """학과글이면 same-major, 아니면 parent_board.comment_access_mask."""
    if is_major_article(article):
        return _is_same_major(user, article.related_major_id)
    return article.parent_board.group_has_access_permission(
        BoardAccessPermissionType.COMMENT, user.profile.group
    )


def deny_non_same_major_access(user, article) -> bool:
    """학과글이고 다른 학과면 True (차단). 일반글은 False (통과)."""
    if not is_major_article(article):
        return False
    return not _is_same_major(user, article.related_major_id)


def deny_non_same_major_comment_access(user, comment) -> bool:
    """학과글에 달린 댓글에 다른 학과 유저가 행위하려 하면 True (차단)."""
    parent = comment.parent_article
    if parent is None and comment.parent_comment is not None:
        parent = comment.parent_comment.parent_article
    if parent is None:
        return False
    return deny_non_same_major_access(user, parent)
