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
    # `related_course`는 source term이며 board scope는 group이 결정한다.
    return article is not None and article.related_course_group_id is not None


def _is_enrolled_in_group(user, group_id) -> bool:
    """User가 group 내 한 term이라도 수강했다면 `True`를 반환한다.
    Past enrollment를 포함해 `IsEnrolledInCourseGroup`과 같은 기준을 적용한다."""
    from apps.course.models import CourseEnrollment

    if group_id is None:
        return False
    return CourseEnrollment.objects.filter(
        user=user, course__group_id=group_id
    ).exists()


def can_read_article(user, article) -> bool:
    """Course article은 enrollment, 그 외에는 `read_access_mask`로 검사한다."""
    if is_course_article(article):
        return _is_enrolled_in_group(user, article.related_course_group_id)
    return article.parent_board.group_has_access_permission(
        BoardAccessPermissionType.READ, user.profile.group
    )


def can_comment_on_article(user, article) -> bool:
    """Course article은 enrollment, 그 외에는 `comment_access_mask`로 검사한다."""
    if is_course_article(article):
        return _is_enrolled_in_group(user, article.related_course_group_id)
    return article.parent_board.group_has_access_permission(
        BoardAccessPermissionType.COMMENT, user.profile.group
    )


def deny_unenrolled_course_access(user, article) -> bool:
    """Course article에 접근한 unenrolled user만 `True`를 반환한다.
    Board mask가 없는 ViewSet에서 추가 access guard로 사용한다."""
    if not is_course_article(article):
        return False
    return not _is_enrolled_in_group(user, article.related_course_group_id)


def deny_unenrolled_comment_access(user, comment) -> bool:
    """Course article의 comment에 unenrolled user가 접근하면 `True`를 반환한다."""
    parent = comment.parent_article
    if parent is None and comment.parent_comment is not None:
        parent = comment.parent_comment.parent_article
    if parent is None:
        return False
    return deny_unenrolled_course_access(user, parent)
