"""과목게시판 접근 권한 체크 헬퍼.

두 종류의 헬퍼를 둔다:

- `can_*` : 원래 board mask 검사를 하던 곳에서 과목글일 때 enrollment 로
  대체하는 룰. 예) Article vote_* (ArticleReadPermission 가 mask 검사),
  Comment create (parent_board.comment_access_mask 검사) 같은 곳.
- `deny_unenrolled_*` : 원래 mask 검사가 없던 곳 (Scrap/Report/Comment vote
  등) 에서 과목글일 때만 추가로 enrollment 검사를 끼운다. 일반글에는 새로
  검사 추가하지 않아 기존 동작이 그대로 보존된다.
"""

from __future__ import annotations

from apps.core.models.board import BoardAccessPermissionType


def is_course_article(article) -> bool:
    return article is not None and article.related_course_id is not None


def _is_enrolled(user, course_id: int) -> bool:
    from apps.course.models import CourseEnrollment

    return CourseEnrollment.objects.filter(user=user, course_id=course_id).exists()


def can_read_article(user, article) -> bool:
    """과목글이면 enrollment, 아니면 parent_board.read_access_mask."""
    if is_course_article(article):
        return _is_enrolled(user, article.related_course_id)
    return article.parent_board.group_has_access_permission(
        BoardAccessPermissionType.READ, user.profile.group
    )


def can_comment_on_article(user, article) -> bool:
    """과목글이면 enrollment, 아니면 parent_board.comment_access_mask."""
    if is_course_article(article):
        return _is_enrolled(user, article.related_course_id)
    return article.parent_board.group_has_access_permission(
        BoardAccessPermissionType.COMMENT, user.profile.group
    )


def deny_unenrolled_course_access(user, article) -> bool:
    """과목글이고 비-수강자면 True (차단). 그 외엔 False (통과).

    원래 board mask 검사가 없던 viewset (Scrap, Report) 에서 과목글에만 추가
    검사를 넣기 위함. 일반글은 항상 False 반환해 기존 동작이 변하지 않는다.
    """
    if not is_course_article(article):
        return False
    return not _is_enrolled(user, article.related_course_id)


def deny_unenrolled_comment_access(user, comment) -> bool:
    """과목글에 달린 댓글에 비-수강자가 행위하려 하면 True (차단)."""
    parent = comment.parent_article
    if parent is None and comment.parent_comment is not None:
        parent = comment.parent_comment.parent_article
    if parent is None:
        return False
    return deny_unenrolled_course_access(user, parent)
