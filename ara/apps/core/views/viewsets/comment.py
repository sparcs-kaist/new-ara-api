from rest_framework import status, viewsets, response, decorators, serializers, permissions

from ara.classes.viewset import ActionAPIViewSet

from apps.core.models import Comment, CommentDeleteLog, Block
from apps.core.filters.comment import CommentFilter
from apps.core.permissions.comment import CommentPermission
from apps.core.serializers.comment import CommentSerializer, \
    CommentCreateActionSerializer, CommentUpdateActionSerializer


class CommentViewSet(viewsets.ModelViewSet, ActionAPIViewSet):
    queryset = Comment.objects.select_related(
        'attachment',
        'created_by',
    )
    filter_class = CommentFilter
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

    def get_queryset(self):
        queryset = super(CommentViewSet, self).get_queryset()

        if self.action == 'best':
            queryset = queryset.filter(
                best__isnull=False,
            )

        queryset = queryset.exclude(
            created_by__in=[block.user for block in Block.objects.filter(blocked_by=self.request.user)]
        )

        return queryset

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
        )

    def perform_update(self, serializer):
        from apps.core.models import CommentUpdateLog

        instance = serializer.instance

        CommentUpdateLog.objects.create(
            content=instance.content,
            attachment=instance.attachment,
            parent_comment=instance,
            updated_by=self.request.user,
        )

        return super(CommentViewSet, self).perform_update(serializer)

    def perform_destroy(self, instance):
        CommentDeleteLog.objects.create(
            deleted_by=self.request.user,
            comment=instance,
        )

        return super(CommentViewSet, self).perform_destroy(instance)

    @decorators.list_route(methods=['get'])
    def best(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    @decorators.detail_route(methods=['post'])
    def vote_cancel(self, request, *args, **kwargs):
        from apps.core.models import Vote

        comment = self.get_object()

        Vote.objects.filter(
            created_by=request.user,
            parent_comment=comment,
        ).delete()

        comment.update_vote_status()

        return response.Response(status=status.HTTP_200_OK)

    @decorators.detail_route(methods=['post'])
    def vote_positive(self, request, *args, **kwargs):
        from apps.core.models import Vote

        comment = self.get_object()

        vote, created = Vote.objects.get_or_create(
            created_by=request.user,
            parent_comment=comment,
            defaults={
                'is_positive': True,
            },
        )

        if not created:
            vote.is_positive = True
            vote.save()

        comment.update_vote_status()

        return response.Response(status=status.HTTP_200_OK)

    @decorators.detail_route(methods=['post'])
    def vote_negative(self, request, *args, **kwargs):
        from apps.core.models import Vote

        comment = self.get_object()

        vote, created = Vote.objects.get_or_create(
            created_by=request.user,
            parent_comment=comment,
            defaults={
                'is_positive': False,
            },
        )

        if not created:
            vote.is_positive = False
            vote.save()

        comment.update_vote_status()

        return response.Response(status=status.HTTP_200_OK)
