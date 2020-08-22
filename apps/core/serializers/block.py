from django.utils.translation import gettext
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
    class Meta(BaseBlockSerializer.Meta):
        read_only_fields = (
            'blocked_by',
        )

