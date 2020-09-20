from rest_framework import mixins, status, response, decorators, serializers, permissions

from ara.classes.viewset import ActionAPIViewSet

from apps.core.models import (
    Comment,
    CommentDeleteLog,
    Vote,
)
from apps.core.filters.comment import CommentFilter
from apps.core.permissions.comment import CommentPermission
from apps.core.serializers.comment import (
    CommentSerializer,
    CommentCreateActionSerializer,
    CommentUpdateActionSerializer,
)


class CommentViewSet(mixins.CreateModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.DestroyModelMixin,
                     ActionAPIViewSet):
    queryset = Comment.objects.select_related(
        'attachment',
        'created_by',
    )
    filterset_class = CommentFilter
    serializer_class = CommentSerializer
    action_serializer_class = {
        'create': CommentCreateActionSerializer,
        'update': CommentUpdateActionSerializer,
        'partial_update': CommentUpdateActionSerializer,
        'vote_positive': serializers.Serializer,
        'vote_negative': serializers.Serializer,
    }
    permission_classes = (
        CommentPermission,
    )
    action_permission_classes = {
        'vote_cancel': (
            permissions.IsAuthenticated,
        ),
        'vote_positive': (
            permissions.IsAuthenticated,
        ),
        'vote_negative': (
            permissions.IsAuthenticated,
        ),
    }

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
        )

    def perform_update(self, serializer):
        from apps.core.models import CommentUpdateLog

        instance = serializer.instance

        CommentUpdateLog.objects.create(
            updated_by=self.request.user,
            comment=instance,
        )

        return super().perform_update(serializer)

    def perform_destroy(self, instance):
        CommentDeleteLog.objects.create(
            deleted_by=self.request.user,
            comment=instance,
        )

        return super().perform_destroy(instance)

    @decorators.action(detail=True, methods=['post'])
    def vote_cancel(self, request, *args, **kwargs):
        comment = self.get_object()

        Vote.objects.filter(
            voted_by=request.user,
            parent_comment=comment,
        ).delete()

        comment.update_vote_status()

        return response.Response(status=status.HTTP_200_OK)

    @decorators.action(detail=True, methods=['post'])
    def vote_positive(self, request, *args, **kwargs):
        comment = self.get_object()

        Vote.objects.update_or_create(
            voted_by=request.user,
            parent_comment=comment,
            defaults={
                'is_positive': True,
            },
        )

        comment.update_vote_status()

        return response.Response(status=status.HTTP_200_OK)

    @decorators.action(detail=True, methods=['post'])
    def vote_negative(self, request, *args, **kwargs):
        comment = self.get_object()

        Vote.objects.update_or_create(
            voted_by=request.user,
            parent_comment=comment,
            defaults={
                'is_positive': False,
            },
        )

        comment.update_vote_status()

        return response.Response(status=status.HTTP_200_OK)
