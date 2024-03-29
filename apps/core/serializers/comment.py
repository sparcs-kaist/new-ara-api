from rest_framework import serializers

from apps.core.models import Block, Comment, CommentHiddenReason
from apps.core.models.board import NameType
from apps.core.serializers.mixins.hidden import (
    HiddenSerializerFieldMixin,
    HiddenSerializerMixin,
)
from apps.user.serializers.user import PublicUserSerializer
from ara.classes.serializers import MetaDataModelSerializer


class BaseCommentSerializer(HiddenSerializerMixin, MetaDataModelSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.CAN_OVERRIDE_REASONS = [CommentHiddenReason.BLOCKED_USER_CONTENT]

    class Meta:
        model = Comment
        exclude = ("attachment",)

    @staticmethod
    def get_my_vote(obj) -> bool | None:
        if not obj.vote_set.exists():
            return None

        my_vote = obj.vote_set.all()[0]

        return my_vote.is_positive

    def get_content(self, obj) -> str | None:
        if self.visible_verdict(obj):
            return obj.content
        return None

    def get_created_by(self, obj) -> dict:
        if obj.name_type in (NameType.ANONYMOUS, NameType.REALNAME):
            return obj.postprocessed_created_by
        else:
            data = PublicUserSerializer(obj.postprocessed_created_by).data
            data["is_blocked"] = Block.is_blocked(
                blocked_by=self.context["request"].user, user=obj.created_by
            )
            return data


class CommentSerializer(HiddenSerializerFieldMixin, BaseCommentSerializer):
    from apps.user.serializers.user import PublicUserSerializer

    my_vote = serializers.SerializerMethodField(
        read_only=True,
    )
    is_mine = serializers.SerializerMethodField(
        read_only=True,
    )
    content = serializers.SerializerMethodField(
        read_only=True,
    )
    created_by = serializers.SerializerMethodField(
        read_only=True,
    )


class CommentListActionSerializer(HiddenSerializerFieldMixin, BaseCommentSerializer):
    from apps.user.serializers.user import PublicUserSerializer

    my_vote = serializers.SerializerMethodField(
        read_only=True,
    )
    is_mine = serializers.SerializerMethodField(
        read_only=True,
    )
    content = serializers.SerializerMethodField(
        read_only=True,
    )
    created_by = serializers.SerializerMethodField(
        read_only=True,
    )


class CommentNestedCommentListActionSerializer(CommentListActionSerializer):
    pass


class ArticleNestedCommentListActionSerializer(CommentListActionSerializer):
    comments = CommentNestedCommentListActionSerializer(
        many=True,
        read_only=True,
        source="comment_set",
    )


class CommentCreateActionSerializer(BaseCommentSerializer):
    class Meta(BaseCommentSerializer.Meta):
        read_only_fields = (
            "positive_vote_count",
            "negative_vote_count",
            "created_by",
        )

    created_by = serializers.SerializerMethodField(
        read_only=True,
    )


class CommentUpdateActionSerializer(BaseCommentSerializer):
    class Meta(BaseCommentSerializer.Meta):
        read_only_fields = (
            "name_type",
            "positive_vote_count",
            "negative_vote_count",
            "created_by",
            "parent_article",
            "parent_comment",
        )

    from apps.user.serializers.user import PublicUserSerializer

    created_by = PublicUserSerializer(
        read_only=True,
    )
