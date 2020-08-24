from django.core.exceptions import ValidationError
from django.utils.translation import gettext
from django.utils import timezone

from ara.classes.serializers import MetaDataModelSerializer

from apps.core.models import Block


class BaseBlockSerializer(MetaDataModelSerializer):
    def validate_user(self, value):
        if self.context['request'].user and self.context['request'].user == value:
            raise ValidationError(gettext('Cannot block yourself'))
        return value

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
    class Meta(BaseBlockSerializer.Meta):
        read_only_fields = (
            'blocked_by',
        )

    def create(self, validated_data):
        # 이미 차단 기록이 존재할 경우 IntegrityError 를 띄우지 않고 생성 시간만 변경하도록 함
        block, _ = Block.objects.update_or_create(
            **validated_data,
            defaults={
                'created_at': timezone.now()
            }
        )
        return block
