from ara.classes.serializers import MetaDataModelSerializer

from apps.core.models import Block
from apps.user.serializers.user import PublicUserSerializer


class BaseBlockSerializer(MetaDataModelSerializer):
    class Meta:
        model = Block
        fields = '__all__'


class BlockSerializer(BaseBlockSerializer):
    class Meta(BaseBlockSerializer.Meta):
        read_only_fields = (
            'blocked_by',
        )

    user = PublicUserSerializer(
        read_only=True,
    )


class BlockCreateActionSerializer(BaseBlockSerializer):
    pass
