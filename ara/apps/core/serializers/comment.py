from rest_framework import serializers

from apps.core.models import Comment
from apps.core.serializers.comment_log import CommentUpdateLogSerializer
from apps.core.serializers.report import ReportSerializer


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
        if not obj.report_set.exists():
            return None

        my_report = obj.report_set.all()[0]

        return ReportSerializer(my_report).data


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
            'use_signature',
            'positive_vote_count',
            'negative_vote_count',
            'created_by',
            'parent_article',
            'parent_comment',
            'created_at',
            'updated_at',
            'deleted_at',
        )
