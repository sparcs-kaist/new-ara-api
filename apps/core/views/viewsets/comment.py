from django.conf import settings

from django.utils.translation import gettext
from rest_framework import mixins, status, response, decorators, serializers, permissions

from ara.classes.viewset import ActionAPIViewSet

from apps.core.models import (
    Comment,
    CommentDeleteLog,
    Vote,
    Article,
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

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        parent_article_id = self.request.data.get('parent_article')
        parent_article = parent_article_id and Article.objects.filter(id=parent_article_id).first()
        parent_article_is_anonymous = (parent_article and parent_article.is_anonymous) or False

        parent_comment_id = self.request.data.get('parent_comment')
        parent_comment = parent_comment_id and Comment.objects.filter(id=parent_comment_id).first()
        parent_comment_is_anonymous = (parent_comment and parent_comment.is_anonymous) or False

        serializer.save(
            created_by=self.request.user,
            is_anonymous=parent_article_is_anonymous or parent_comment_is_anonymous,
        )

    def retrieve(self, request, *args, **kwargs):
        comment = self.get_object()
        override_hidden = 'override_hidden' in self.request.query_params

        serialized = CommentSerializer(comment, context={'request': request, 'override_hidden': override_hidden})
        return response.Response(serialized.data)

    def update(self, request, *args, **kwargs):
        comment = self.get_object()

        if comment.is_hidden_by_reported() or comment.is_deleted():
            return response.Response({'message': gettext('Cannot modify hidden or deleted comments')},
                                     status=status.HTTP_403_FORBIDDEN)

        return super().update(request, *args, **kwargs)

    def perform_update(self, serializer):
        from apps.core.models import CommentUpdateLog

        instance = serializer.instance

        CommentUpdateLog.objects.create(
            updated_by=self.request.user,
            comment=instance,
        )

        return super().perform_update(serializer)

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()

        if comment.is_hidden_by_reported() or comment.is_deleted():
            return response.Response({'message': gettext('Cannot delete hidden or deleted comments')},
                                     status=status.HTTP_403_FORBIDDEN)

        return super().destroy(request, *args, **kwargs)

    def perform_destroy(self, instance):
        CommentDeleteLog.objects.create(
            deleted_by=self.request.user,
            comment=instance,
        )

        return super().perform_destroy(instance)

    @decorators.action(detail=True, methods=['post'])
    def vote_cancel(self, request, *args, **kwargs):
        comment = self.get_object()

        if comment.is_hidden_by_reported() or comment.is_deleted():
            return response.Response({'message': gettext('Cannot cancel vote on comments that are deleted or hidden by reports')},
                                     status=status.HTTP_403_FORBIDDEN)

        Vote.objects.filter(
            voted_by=request.user,
            parent_comment=comment,
        ).delete()

        comment.update_vote_status()

        return response.Response(status=status.HTTP_200_OK)

    @decorators.action(detail=True, methods=['post'])
    def vote_positive(self, request, *args, **kwargs):
        comment = self.get_object()

        if comment.created_by_id == request.user.id:
            return response.Response({'message': gettext('Cannot vote on your own comment')},
                                     status=status.HTTP_403_FORBIDDEN)

        if comment.is_hidden_by_reported() or comment.is_deleted():
            return response.Response({'message': gettext('Cannot vote on comments that are deleted or hidden by reports')},
                                     status=status.HTTP_403_FORBIDDEN)

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

        if comment.created_by_id == request.user.id:
            return response.Response({'message': gettext('Cannot vote on your own comment')},
                                     status=status.HTTP_403_FORBIDDEN)

        if comment.is_hidden_by_reported() or comment.is_deleted():
            return response.Response({'message': gettext('Cannot vote on comments that are deleted or hidden by reports')},
                                     status=status.HTTP_403_FORBIDDEN)

        Vote.objects.update_or_create(
            voted_by=request.user,
            parent_comment=comment,
            defaults={
                'is_positive': False,
            },
        )

        comment.update_vote_status()

        return response.Response(status=status.HTTP_200_OK)
