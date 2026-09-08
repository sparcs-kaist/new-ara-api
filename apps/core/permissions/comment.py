from rest_framework import permissions


class CommentPermission(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        # 과목글 댓글이면 enrollment 검사. 비-수강자가 comment id 만 알면 GET 으로
        # 내용을 볼 수 있던 누수 방지 (defense in depth).
        from apps.course.access import deny_unenrolled_comment_access
        from apps.major.access import (
            deny_non_same_major_comment_access,
            deny_unreadable_major_comment_access,
        )

        if deny_unenrolled_comment_access(request.user, obj):
            return False

        if request.method in permissions.SAFE_METHODS:
            # 학과글 댓글 읽기는 본인 SSO 학과뿐 아니라 즐겨찾기 학과도 허용한다.
            return not deny_unreadable_major_comment_access(request.user, obj)

        # 댓글 수정·삭제는 기존 정책대로 SSO 동일 학과의 작성자(또는 staff)만.
        if deny_non_same_major_comment_access(request.user, obj):
            return False
        return request.user.is_staff or request.user == obj.created_by
