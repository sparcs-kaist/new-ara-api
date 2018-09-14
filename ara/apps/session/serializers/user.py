from django.contrib.auth import get_user_model

from rest_framework import serializers


class BaseUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    class Meta(BaseUserSerializer.Meta):
        fields = '__all__'

    from apps.session.serializers.user_profile import UserProfileSerializer
    profile = UserProfileSerializer()


class UserDetailActionSerializer(serializers.ModelSerializer):
    class Meta(BaseUserSerializer.Meta):
        fields = (
            'id',
            'username',
            'profile',
        )
        read_only_fields = (
            'id',
            'username',
            'profile',
        )

    from apps.session.serializers.user_profile import UserProfileSerializer
    profile = UserProfileSerializer(
        read_only=True,
    )


class PublicUserSerializer(serializers.ModelSerializer):
    class Meta(BaseUserSerializer.Meta):
        fields = (
            'id',
            'email',
            'username',

            'profile',
        )

    from apps.session.serializers.user_profile import PublicUserProfileSerializer
    profile = PublicUserProfileSerializer()
