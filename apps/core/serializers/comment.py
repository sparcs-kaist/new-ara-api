from rest_framework import serializers, exceptions
import typing

from ara.classes.serializers import MetaDataModelSerializer
from apps.user.serializers.user import PublicUserSerializer
from apps.core.models import Comment, Block
from django.utils.translation import gettext


class BaseCommentSerializer(MetaDataModelSerializer):
    class Meta:
        model = Comment
        exclude = ('attachment', )

    @staticmethod
    def get_my_vote(obj) -> typing.Optional[bool]:
        if not obj.vote_set.exists():
            return None

        my_vote = obj.vote_set.all()[0]

        return my_vote.is_positive

    def get_is_mine(self, obj) -> bool:
        return self.context['request'].user == obj.created_by

    def get_is_hidden(self, obj) -> bool:
        if obj.is_hidden_by_reported():
            return False
        elif self.validate_hidden(obj):
            return True

        return False

    def get_why_hidden(self, obj) -> typing.List[dict]:
        errors = self.validate_hidden(obj)

        return [
            {
                'detail': error.detail,
            } for error in errors
        ]

    def get_content(self, obj) -> typing.Union[str, list]:
        if obj.is_deleted():
            return gettext('This comment is deleted')

        if obj.is_hidden_by_reported():
            return gettext('This comment is hidden because it received multiple reports')

        errors = self.validate_hidden(obj)

        if errors:
            return [error.detail for error in errors]

        return obj.content

    def get_hidden_content(self, obj) -> str:
        if obj.is_deleted():
            return gettext('This comment is deleted')
            
        if obj.is_hidden_by_reported():
            return gettext('This comment is hidden because it received multiple reports')
        elif self.validate_hidden(obj):
            return obj.content

        return ''

    def get_created_by(self, obj) -> dict:
        if obj.is_anonymous:
            return obj.postprocessed_created_by
        else:
            data = PublicUserSerializer(obj.postprocessed_created_by).data
            data['is_blocked'] = Block.is_blocked(blocked_by=self.context['request'].user, user=obj.created_by)
            return data

    def validate_hidden(self, obj) -> typing.List[exceptions.ValidationError]:
        errors = []

        if Block.is_blocked(blocked_by=self.context['request'].user, user=obj.created_by):
            errors.append(exceptions.ValidationError(gettext('This article is written by a user you blocked.')))

        return errors


class CommentSerializer(BaseCommentSerializer):
    from apps.user.serializers.user import PublicUserSerializer
    created_by = PublicUserSerializer(
        read_only=True,
    )
    my_vote = serializers.SerializerMethodField(
        read_only=True,
    )
    is_mine = serializers.SerializerMethodField(
        read_only=True,
    )
    is_hidden = serializers.SerializerMethodField(
        read_only=True,
    )
    why_hidden = serializers.SerializerMethodField(
        read_only=True,
    )
    content = serializers.SerializerMethodField(
        read_only=True,
    )
    hidden_content = serializers.SerializerMethodField(
        read_only=True,
    )
    created_by = serializers.SerializerMethodField(
        read_only=True,
    )


class CommentListActionSerializer(BaseCommentSerializer):
    from apps.user.serializers.user import PublicUserSerializer
    created_by = PublicUserSerializer(
        read_only=True,
    )
    my_vote = serializers.SerializerMethodField(
        read_only=True,
    )
    is_mine = serializers.SerializerMethodField(
        read_only=True,
    )
    is_hidden = serializers.SerializerMethodField(
        read_only=True,
    )
    why_hidden = serializers.SerializerMethodField(
        read_only=True,
    )
    content = serializers.SerializerMethodField(
        read_only=True,
    )
    hidden_content = serializers.SerializerMethodField(
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
        source='comment_set',
    )


class CommentCreateActionSerializer(BaseCommentSerializer):
    class Meta(BaseCommentSerializer.Meta):
        read_only_fields = (
            'positive_vote_count',
            'negative_vote_count',
            'created_by',
        )

    from apps.user.serializers.user import PublicUserSerializer
    created_by = PublicUserSerializer(
        read_only=True,
    )


class CommentUpdateActionSerializer(BaseCommentSerializer):
    class Meta(BaseCommentSerializer.Meta):
        read_only_fields = (
            'is_anonymous',
            'positive_vote_count',
            'negative_vote_count',
            'created_by',
            'parent_article',
            'parent_comment',
        )

    from apps.user.serializers.user import PublicUserSerializer
    created_by = PublicUserSerializer(
        read_only=True,
    )
