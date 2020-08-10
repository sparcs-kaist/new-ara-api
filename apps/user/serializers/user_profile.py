from ara.classes.serializers import MetaDataModelSerializer
from django.utils import timezone
from rest_framework import serializers

from apps.user.models import UserProfile


class BaseUserProfileSerializer(MetaDataModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'


class UserProfileSerializer(BaseUserProfileSerializer):
    extra_preferences = serializers.JSONField(
        read_only=True,
    )


class UserProfileUpdateActionSerializer(BaseUserProfileSerializer):
    class Meta(BaseUserProfileSerializer.Meta):
        read_only_fields = (
            'sid',
            'user',
        )

    def validate_nickname(self, value):
        if self.instance and value != self.instance.nickname and not self.instance.can_change_nickname():
            raise serializers.ValidationError('90 days must pass to change your nickname.')
        return value

    def update(self, instance, validated_data):
        if instance and 'nickname' in validated_data and instance.nickname != validated_data:
            validated_data['nickname_updated_at'] = timezone.now()
        return super(BaseUserProfileSerializer, self).update(instance, validated_data)


    extra_preferences = serializers.JSONField()


class PublicUserProfileSerializer(BaseUserProfileSerializer):
    class Meta(BaseUserProfileSerializer.Meta):
        fields = (
            'user_id',
            'picture',
            'nickname',
            'user'
        )
