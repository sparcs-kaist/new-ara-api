from rest_framework import serializers

from apps.core.models import Block


class BaseBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Block
        fields = '__all__'
        read_only_fields = (
            'blocked_by',
            'created_at',
            'updated_at',
            'deleted_at',
        )


class BlockSerializer(BaseBlockSerializer):
    from apps.session.serializers.user import PublicUserSerializer
    user = PublicUserSerializer()


class BlockCreateActionSerializer(BaseBlockSerializer):
    pass
