from rest_framework import serializers

from apps.core.models import Scrap


class ScrapSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scrap
        fields = '__all__'


class ScrapCreateActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scrap
        fields = '__all__'
        read_only_fields = (
            'scrapped_by',
        )
