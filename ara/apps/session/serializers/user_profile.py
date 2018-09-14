from rest_framework import serializers

from ara.classes.serializers import MetaDataModelSerializer

from apps.session.models import UserProfile


class BaseUserProfileSerializer(MetaDataModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'


class UserProfileSerializer(BaseUserProfileSerializer):
    extra_preferences = serializers.JSONField()


class PublicUserProfileSerializer(BaseUserProfileSerializer):
    class Meta(BaseUserProfileSerializer.Meta):
        fields = (
            'id',
            'picture',
            'nickname',
            'user'
        )


class UserProfileUpdateActionSerializer(BaseUserProfileSerializer):
    class Meta(BaseUserProfileSerializer.Meta):
        read_only_fields = (
            'sid',
            'user',
        )

    extra_preferences = serializers.JSONField()
