from rest_framework import serializers

from apps.core.models import Comment, Report, Vote
from apps.core.serializers.comment_log import CommentUpdateLogSerializer
from apps.core.serializers.report import ReportSerializer


class BaseCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = '__all__'

    def get_my_vote(self, obj):
        try:
            return obj.my_vote[0].is_positive

        except IndexError:
            return None

        except AttributeError:
            try:
                return obj.vote_set.get(
                    voted_by=self.context['request'].user,
                ).is_positive

            except Vote.DoesNotExist:
                return None

    def get_my_report(self, obj):
        try:
            return ReportSerializer(
                instance=obj.my_report[0],
            ).data

        except IndexError:
            return None

        except AttributeError:
            try:
                return ReportSerializer(
                    instance=obj.report_set.get(
                        reported_by=self.context['request'].user,
                    ),
                ).data

            except Report.DoesNotExist:
                return None


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


class Depth2CommentSerializer(BaseCommentSerializer):
    pass


class Depth1CommentSerializer(BaseCommentSerializer):
    comments = Depth2CommentSerializer(
        many=True,
        read_only=True,
        source='comment_set',
    )


class CommentCreateActionSerializer(CommentSerializer):
    class Meta(CommentSerializer.Meta):
        read_only_fields = (
            'positive_vote_count',
            'negative_vote_count',
            'created_by',
            'created_at',
            'updated_at',
            'deleted_at',
        )


class CommentUpdateActionSerializer(CommentSerializer):
    class Meta(CommentSerializer.Meta):
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
