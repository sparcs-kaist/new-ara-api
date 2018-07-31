from rest_framework import serializers

from apps.core.models import Report


class BaseReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = '__all__'


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = '__all__'

    from apps.core.serializers.article import BaseArticleSerializer
    parent_article = BaseArticleSerializer()

    from apps.core.serializers.comment import BaseCommentSerializer
    parent_comment = BaseCommentSerializer()


class ReportCreateActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = '__all__'
        read_only_fields = (
            'reported_by',
            'created_at',
            'updated_at',
            'deleted_at',
        )
