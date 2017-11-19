from rest_framework import serializers

from apps.core.models import BlackList


class BlackListSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlackList
        fields = '__all__'



class BlackListCreateActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlackList
        fields = '__all__'
        read_only_fields = (
            'black_from',
        )





