from rest_framework import permissions


class AttachmentPermission(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        if request.method == 'DELETE':
            return request.user.is_staff or all([request.user == article.created_by
                                                 for article in obj.article_set.all()])

        return super(
            AttachmentPermission,
            self).has_object_permission(
            request,
            view,
            obj)
