from rest_framework import serializers

from apps.core.models import Comment


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        exclude = (
            'parent_article',
            'parent_comment',
        )

    from apps.core.serializers.comment_log import CommentUpdateLogSerializer

    my_vote = serializers.SerializerMethodField()
    my_report = serializers.SerializerMethodField()

    comments = serializers.SerializerMethodField()

    comment_update_logs = CommentUpdateLogSerializer(
        many=True,
        source='comment_update_log_set',
    )

    def get_my_vote(self, obj):
        from apps.core.models import Vote

        try:
            return obj.vote_set.get(
                created_by=self.context['request'].user,
            ).is_positive

        except Vote.DoesNotExist:
            return None

    def get_my_report(self, obj):
        from apps.core.models import Report
        from apps.core.serializers.report import ReportSerializer

        try:
            return ReportSerializer(
                instance=obj.report_set.get(
                    reported_by=self.context['request'].user,
                ),
            ).data

        except Report.DoesNotExist:
            return None

    def get_comments(self, obj):
        return CommentSerializer(
            obj.comment_set.all(), many=True,
            ** {'context': {'request': self.context.get('request')}}
        ).data


class CommentCreateActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = (
            'content',
            'is_anonymous',
            'use_signature',
            'parent_article',
            'parent_comment',
            'attachment',
        )


class CommentUpdateActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = (
            'content',
            'attachment',
        )
