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


def is_major_article(article) -> bool:
    return article is not None and article.related_major_id is not None


def user_major_info(user) -> dict | None:
    """SSO kaist_v2_info 에서 학과 정보를 dict 로 추출. 실패 시 None.

    반환: {"std_dept_id": int, "major_name": str, "major_name_eng": str | None}
    """
    profile = getattr(user, "profile", None)
    if profile is None:
        return None
    sso = profile.sso_user_info or {}
    raw = sso.get("kaist_v2_info")
    if not raw:
        return None
    try:
        info = json.loads(raw) if isinstance(raw, str) else raw
    except (ValueError, TypeError, json.JSONDecodeError):
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
    """SSO 의 std_dept_id 를 정수로 반환. 없거나 파싱 실패 시 None."""
    info = user_major_info(user)
    return info["std_dept_id"] if info else None


def get_or_create_major_for_user(user):
    """요청 유저의 SSO 정보로 자기 학과 Major row 를 lazy get_or_create.

    Major 는 사전 시드하지 않는다. 권한(IsSameMajor)이 "URL 의 std_dept_id ==
    유저 SSO 의 std_dept_id" 를 이미 보장하므로, 유저 SSO 의 학과명으로 채워도
    URL 이 가리키는 학과와 항상 일치한다. board.py 의 get_major_board_id 와
    같은 lazy 생성 패턴.
    """
    from apps.major.models import Major, UserMajor
    from apps.major.models.major import get_major_code

    info = user_major_info(user)
    if info is None:
        return None
    major, _ = Major.objects.get_or_create(
        std_dept_id=info["std_dept_id"],
        defaults={
            "major_name": info["major_name"],
            "major_name_eng": info["major_name_eng"],
            # SSO 는 코드를 주지 않으므로 학과 이름으로 매핑표에서 찾아 채운다.
            "major_code": get_major_code(info["major_name"]),
        },
    )
    # 홈 학과도 UserMajor 에 담아 '독자'로 집계한다 (readers_count 가 전체 독자
    # 수가 되도록). UniqueConstraint(user, major) 로 멱등하다.
    UserMajor.objects.get_or_create(user=user, major=major)
    return major


def _is_same_major(user, std_dept_id) -> bool:
    """user 의 SSO std_dept_id 가 대상 학과(std_dept_id, = Major PK) 와 같은가.

    쓰기(글/댓글/투표/스크랩/신고) 권한 판정에 쓴다. Major row 존재 여부와
    무관하게 SSO 값만 비교한다. row 는 실제 접근 시 viewset 에서 lazy 생성되므로,
    여기서 존재를 요구하면 첫 접근이 막힌다.
    """
    user_dept_id = user_major_id(user)
    if user_dept_id is None:
        return False
    try:
        return int(std_dept_id) == user_dept_id
    except (TypeError, ValueError):
        return False


def user_added_major_ids(user) -> set[int]:
    """user 가 add 해 둔 타 학과들의 std_dept_id(= Major PK) 집합."""
    from apps.major.models import UserMajor

    return set(
        UserMajor.objects.filter(user=user).values_list("major_id", flat=True)
    )


def can_read_major(user, std_dept_id) -> bool:
    """user 가 대상 학과 게시판을 '읽을' 수 있는가.

    읽기 = 내 SSO 학과 OR 내가 add 한 학과. 쓰기와 달리 add 한 타 학과도 허용.
    """
    if _is_same_major(user, std_dept_id):
        return True
    try:
        std = int(std_dept_id)
    except (TypeError, ValueError):
        return False
    from apps.major.models import UserMajor

    return UserMajor.objects.filter(user=user, major_id=std).exists()


def can_read_article(user, article) -> bool:
    """학과글이면 읽기 권한(내 학과 OR add 한 학과), 아니면 parent_board.read_access_mask."""
    if is_major_article(article):
        return can_read_major(user, article.related_major_id)
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
