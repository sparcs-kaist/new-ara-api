from rest_framework import viewsets

from ara.classes.viewset import ActionAPIViewSet

from apps.core.models import Comment
from apps.core.filters.comment import CommentFilter
from apps.core.permissions.comment import CommentPermission
from apps.core.serializers.comment import CommentSerializer, \
    CommentCreateActionSerializer, CommentUpdateActionSerializer


class CommentViewSet(viewsets.ModelViewSet, ActionAPIViewSet):
    queryset = Comment.objects.all()
    filter_class = CommentFilter
    serializer_class = CommentSerializer
    action_serializer_class = {
        'create': CommentCreateActionSerializer,
        'update': CommentUpdateActionSerializer,
        'partial_update': CommentUpdateActionSerializer,
    }
    permission_classes = (
        CommentPermission,
    )

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
        )

    def perform_update(self, serializer):
        instance = serializer.instance
        from apps.core.models import CommentUpdateLog
        CommentUpdateLog.objects.create(
            content = instance.content,
            attachment = instance.attachment,
            parent_comment = instance,
            updated_by = self.request.user,
        )
        return super(CommentViewSet, self).perform_update(serializer)



