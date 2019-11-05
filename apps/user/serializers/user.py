from django.contrib.auth import get_user_model

from rest_framework import serializers

from apps.user.serializers.user_profile import UserProfileSerializer
from apps.user.serializers.user_profile import PublicUserProfileSerializer


class BaseUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = '__all__'


class UserSerializer(BaseUserSerializer):
    profile = UserProfileSerializer(
        read_only=True,
    )


class UserDetailActionSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        fields = (
            'id',
            'username',
            'profile',
        )

    profile = UserProfileSerializer(
        read_only=True,
    )


class PublicUserSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        fields = (
            'id',
            'email',
            'username',
            'profile',
        )

    profile = PublicUserProfileSerializer(
        read_only=True,
    )
