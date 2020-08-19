from rest_framework import serializers

from ara.classes.serializers import MetaDataModelSerializer

from apps.core.models import Block


class BaseBlockSerializer(MetaDataModelSerializer):
    class Meta:
        model = Block
        fields = '__all__'


class BlockSerializer(BaseBlockSerializer):
    class Meta(BaseBlockSerializer.Meta):
        read_only_fields = (
            'blocked_by',
        )

    from apps.user.serializers.user import PublicUserSerializer
    user = PublicUserSerializer(
        read_only=True,
    )


class BlockCreateActionSerializer(BaseBlockSerializer):
    def validate(self, data):
        blocked_by = data.get('blocked_by')
        user = data.get('user')
        if Block.objects.filter(blocked_by=blocked_by, user=user).exists():
            raise serializers.ValidationError(f'이미 차단한 유저입니다.')
        return data
