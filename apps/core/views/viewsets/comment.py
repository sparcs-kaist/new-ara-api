from django.shortcuts import get_object_or_404
from django.utils.translation import gettext
from rest_framework import (
    decorators,
    mixins,
    permissions,
    response,
    serializers,
    status,
)

from apps.core.filters.comment import CommentFilter
from apps.core.models import Article, Comment, CommentDeleteLog, UserProfile, Vote
from apps.core.models.board import NameType
from apps.core.permissions.comment import CommentPermission
from apps.core.serializers.comment import (
    CommentCreateActionSerializer,
    CommentSerializer,
    CommentUpdateActionSerializer,
)
from ara.classes.viewset import ActionAPIViewSet


class CommentViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    ActionAPIViewSet,
):
    queryset = Comment.objects.select_related(
        "attachment",
        "created_by",
    )
    filterset_class = CommentFilter
    serializer_class = CommentSerializer
    action_serializer_class = {
        "create": CommentCreateActionSerializer,
        "update": CommentUpdateActionSerializer,
        "partial_update": CommentUpdateActionSerializer,
        "vote_positive": serializers.Serializer,
        "vote_negative": serializers.Serializer,
    }
    permission_classes = (CommentPermission,)
    action_permission_classes = {
        "vote_cancel": (permissions.IsAuthenticated,),
        "vote_positive": (permissions.IsAuthenticated,),
        "vote_negative": (permissions.IsAuthenticated,),
    }

    def create(self, request, *args, **kwargs):
        if self.request.data.get("parent_article") is None:
            comment_queryset = Comment.objects.all()
            parent_comment = get_object_or_404(
                comment_queryset, pk=self.request.data["parent_comment"]
            )
            parent_article = parent_comment.parent_article
        else:
            article_queryset = Article.objects.all()
            parent_article = get_object_or_404(
                article_queryset, pk=self.request.data["parent_article"]
            )
        # TODO: Use CommentPermission for permission checking logic
        # self.check_object_permissions(request, parent_article)

        # Check permission
        if parent_article.parent_board.permission_list_by_user(request.user).COMMENT:
            return super().create(request, *args, **kwargs)
        return response.Response(
            {"message": gettext("Permission denied")}, status=status.HTTP_403_FORBIDDEN
        )

    def perform_create(self, serializer):
        parent_article_id: int | None = self.request.data.get("parent_article")

        if parent_article_id is not None:
            parent_article: Article = parent_article_id and Article.objects.get(
                id=parent_article_id
            )
        else:
            parent_comment_id: int = self.request.data.get("parent_comment")
            parent_comment: Comment = parent_comment_id and Comment.objects.get(
                id=parent_comment_id
            )
            parent_article = parent_comment.parent_article

        # print(parent_article)

        created_by = self.request.user
        is_school_admin = UserProfile.objects.get(user_id=created_by).is_school_admin

        if is_school_admin and parent_article.name_type != NameType.ANONYMOUS:
            name_type = NameType.REGULAR
        else:
            name_type = parent_article.name_type

        serializer.save(
            created_by=created_by,
            name_type=name_type,
        )

    def retrieve(self, request, *args, **kwargs):
        comment = self.get_object()
        override_hidden = "override_hidden" in self.request.query_params

        serialized = CommentSerializer(
            comment, context={"request": request, "override_hidden": override_hidden}
        )
        return response.Response(serialized.data)

    def update(self, request, *args, **kwargs):
        comment = self.get_object()

        if comment.is_hidden_by_reported() or comment.is_deleted():
            return response.Response(
                {"message": gettext("Cannot modify hidden or deleted comments")},
                status=status.HTTP_403_FORBIDDEN,
            )

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
            return response.Response(
                {"message": gettext("Cannot delete hidden or deleted comments")},
                status=status.HTTP_403_FORBIDDEN,
            )

        return super().destroy(request, *args, **kwargs)

    def perform_destroy(self, instance):
        CommentDeleteLog.objects.create(
            deleted_by=self.request.user,
            comment=instance,
        )

        return super().perform_destroy(instance)

    @decorators.action(detail=True, methods=["post"])
    def vote_cancel(self, request, *args, **kwargs):
        comment = self.get_object()

        if comment.is_hidden_by_reported() or comment.is_deleted():
            return response.Response(
                {
                    "message": gettext(
                        "Cannot cancel vote on comments that are deleted or hidden by reports"
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        Vote.objects.filter(
            voted_by=request.user,
            parent_comment=comment,
        ).delete()

        comment.update_vote_status()

        return response.Response(status=status.HTTP_200_OK)

    @decorators.action(detail=True, methods=["post"])
    def vote_positive(self, request, *args, **kwargs):
        comment = self.get_object()

        if comment.created_by_id == request.user.id:
            return response.Response(
                {"message": gettext("Cannot vote on your own comment")},
                status=status.HTTP_403_FORBIDDEN,
            )

        if comment.is_hidden_by_reported() or comment.is_deleted():
            return response.Response(
                {
                    "message": gettext(
                        "Cannot vote on comments that are deleted or hidden by reports"
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        Vote.objects.update_or_create(
            voted_by=request.user,
            parent_comment=comment,
            defaults={
                "is_positive": True,
            },
        )

        comment.update_vote_status()

        return response.Response(status=status.HTTP_200_OK)

    @decorators.action(detail=True, methods=["post"])
    def vote_negative(self, request, *args, **kwargs):
        comment = self.get_object()

        if comment.created_by_id == request.user.id:
            return response.Response(
                {"message": gettext("Cannot vote on your own comment")},
                status=status.HTTP_403_FORBIDDEN,
            )

        if comment.is_hidden_by_reported() or comment.is_deleted():
            return response.Response(
                {
                    "message": gettext(
                        "Cannot vote on comments that are deleted or hidden by reports"
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        Vote.objects.update_or_create(
            voted_by=request.user,
            parent_comment=comment,
            defaults={
                "is_positive": False,
            },
        )

        comment.update_vote_status()

        return response.Response(status=status.HTTP_200_OK)
