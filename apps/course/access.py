"""과목게시판 접근 권한 체크 헬퍼.

기존 Article/Comment 도메인의 viewset 들이 board mask 기반으로 권한을
검사하는데, 과목게시판 글은 dummy board (mask 0) 를 쓰기 때문에 이 룰을
그대로 두면 댓글/투표/신고 가 전부 막힌다. 과목글일 때 enrollment 로
fallback 하기 위한 분기를 한 곳에 모은다.
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


def can_act_on_comment(user, comment) -> bool:
    """댓글에 read/vote 가능한지. 부모 article 의 룰을 따른다."""
    parent = comment.parent_article
    if parent is None and comment.parent_comment is not None:
        parent = comment.parent_comment.parent_article
    if parent is None:
        return False
    return can_read_article(user, parent)
