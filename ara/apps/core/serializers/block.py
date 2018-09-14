from ara.classes.serializers import MetaDataModelSerializer

from apps.core.models import Block


class BaseBlockSerializer(MetaDataModelSerializer):
    class Meta:
        model = Block
        fields = '__all__'
        read_only_fields = (
            'blocked_by',
        )


class BlockSerializer(BaseBlockSerializer):
    from apps.session.serializers.user import PublicUserSerializer
    user = PublicUserSerializer()


class BlockCreateActionSerializer(BaseBlockSerializer):
    pass
