from rest_framework import permissions


class CommentPermission(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        # 과목글 댓글이면 enrollment 검사. 비-수강자가 comment id 만 알면 GET 으로
        # 내용을 볼 수 있던 누수 방지 (defense in depth).
        from apps.course.access import deny_unenrolled_comment_access
        from apps.major.access import deny_non_same_major_comment_access

        if deny_unenrolled_comment_access(request.user, obj):
            return False
        if deny_non_same_major_comment_access(request.user, obj):
            return False

        if request.method not in permissions.SAFE_METHODS:
            return request.user.is_staff or request.user == obj.created_by

        return super().has_object_permission(request, view, obj)
