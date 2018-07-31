from rest_framework import serializers, exceptions

from apps.core.models import Comment
from apps.core.serializers.comment_log import CommentUpdateLogSerializer


class BaseCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = '__all__'

    def get_my_vote(self, obj):
        if not obj.vote_set.exists():
            return None

        my_vote = obj.vote_set.all()[0]

        return my_vote.is_positive

    def get_my_report(self, obj):
        from apps.core.serializers.report import ReportSerializer

        if not obj.report_set.exists():
            return None

        my_report = obj.report_set.all()[0]

        return ReportSerializer(my_report).data

    def get_is_hidden(self, obj):
        if self.validate_hidden(obj):
            return True

        return False

    def get_why_hidden(self, obj):
        errors = self.validate_hidden(obj)

        return [
            {
                'detail': error.detail,
            } for error in errors
        ]

    def get_content(self, obj):
        errors = self.validate_hidden(obj)

        if errors:
            return [error.detail for error in errors]

        return obj.content

    def get_hidden_content(self, obj):
        if self.validate_hidden(obj):
            return obj.content

        return ''

    def validate_hidden(self, obj):
        errors = []

        if obj.created_by.blocked_by_set.exists():
            errors.append(exceptions.ValidationError('차단한 사용자의 게시물입니다.'))

        return errors


class CommentSerializer(BaseCommentSerializer):
    comment_update_logs = CommentUpdateLogSerializer(
        many=True,
        read_only=True,
        source='comment_update_log_set',
    )

    my_vote = serializers.SerializerMethodField(
        read_only=True,
    )
    my_report = serializers.SerializerMethodField(
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


class Depth2CommentSerializer(CommentSerializer):
    pass


class Depth1CommentSerializer(CommentSerializer):
    comments = Depth2CommentSerializer(
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
            'created_at',
            'updated_at',
            'deleted_at',
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
            'created_at',
            'updated_at',
            'deleted_at',
        )
