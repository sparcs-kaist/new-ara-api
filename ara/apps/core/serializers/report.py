from rest_framework import serializers

from apps.core.models import Report


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report

class ReportCreateActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = (
            'parent_article',
            'parent_comment',
            'content',
        )


