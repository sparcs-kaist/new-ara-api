from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils.translation import gettext
from rest_framework import serializers

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
        try:
            return super().create(validated_data)
        except IntegrityError:
            raise serializers.ValidationError(gettext("This user is already blocked."))
