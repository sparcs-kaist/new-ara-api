from rest_framework import serializers

from apps.core.models import Report


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        field = '__all__'

class ReportCreateActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = (
            'parent_article',
            'parent_comment',
            'content',
        )


