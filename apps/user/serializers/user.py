from django.contrib.auth import get_user_model
from rest_framework import serializers


class BaseUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = "__all__"


class PublicUserSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        fields = (
            "id",
            "username",
            "profile",
        )

    from apps.user.serializers.user_profile import PublicUserProfileSerializer

    profile = PublicUserProfileSerializer(
        read_only=True,
    )
