from rest_framework import serializers

from apps.core.models import Report


class BaseReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = '__all__'


class ReportSerializer(BaseReportSerializer):
    from apps.core.serializers.article import BaseArticleSerializer
    parent_article = BaseArticleSerializer()

    from apps.core.serializers.comment import BaseCommentSerializer
    parent_comment = BaseCommentSerializer()

    from apps.session.serializers.user import PublicUserSerializer
    reported_by = PublicUserSerializer()


class ReportCreateActionSerializer(BaseReportSerializer):
    class Meta(BaseReportSerializer.Meta):
        read_only_fields = (
            'reported_by',
            'created_at',
            'updated_at',
            'deleted_at',
        )
