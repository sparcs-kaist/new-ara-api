from rest_framework import serializers

from apps.core.models import Report


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = '__all__'


class ReportCreateActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = '__all__'
        read_only_fields = (
            'scrapped_by',
        )
