from rest_framework import serializers, exceptions
import typing

from ara.classes.serializers import MetaDataModelSerializer
from apps.user.serializers.user import PublicUserSerializer
from apps.core.models import Comment, Block, CommentHiddenReason
from django.utils.translation import gettext


CAN_OVERRIDE_REASONS = [
    CommentHiddenReason.BLOCKED_USER_CONTENT
]


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
        return not self.visible_verdict(obj)

    def get_why_hidden(self, obj) -> typing.List[str]:
        _, _, reasons = self.hidden_info(obj)
        return [reason.value for reason in reasons]
        
    def get_content(self, obj) -> typing.Optional[str]:
        if self.visible_verdict(obj):
            return obj.content
        return None

    def get_created_by(self, obj) -> dict:
        if obj.is_anonymous:
            return obj.postprocessed_created_by
        else:
            data = PublicUserSerializer(obj.postprocessed_created_by).data
            data['is_blocked'] = Block.is_blocked(blocked_by=self.context['request'].user, user=obj.created_by)
            return data

    def get_can_override_hidden(self, obj) -> typing.Optional[bool]:
        hidden, can_override, _ = self.hidden_info(obj)
        if not hidden:
            return
        return can_override

    def visible_verdict(self, obj):
        hidden, can_override, _ = self.hidden_info(obj)
        return not hidden or (can_override and self.requested_override_hidden)

    @property
    def requested_override_hidden(self):
        request = self.context['request']
        override_hidden = 'override_hidden' in request.query_params
        return override_hidden

    # TODO: 전체 캐싱 (여기에 이 메소드 자체가 없도록 디자인을 바꿔야할듯)
    def hidden_info(self, obj) -> typing.Tuple[bool, bool, typing.List[CommentHiddenReason]]:
        reasons: typing.List[CommentHiddenReason] = []
        request = self.context['request']

        if Block.is_blocked(blocked_by=request.user, user=obj.created_by):
            reasons.append(CommentHiddenReason.BLOCKED_USER_CONTENT)
        if obj.is_hidden_by_reported():
            reasons.append(CommentHiddenReason.REPORTED_CONTENT)
        if obj.is_deleted():
            reasons.append(CommentHiddenReason.DELETED_CONTENT)

        cannot_override_reasons = [reason for reason in reasons if reason not in CAN_OVERRIDE_REASONS]
        can_override = len(cannot_override_reasons) == 0

        return len(reasons) > 0, can_override, reasons


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
    can_override_hidden = serializers.SerializerMethodField(
        read_only=True,
    )
    content = serializers.SerializerMethodField(
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
