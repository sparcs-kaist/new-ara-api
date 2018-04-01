from django.contrib.auth import get_user_model

from rest_framework import serializers


class UserDetailActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
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
