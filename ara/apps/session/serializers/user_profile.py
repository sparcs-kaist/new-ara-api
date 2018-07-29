from rest_framework import serializers

from apps.session.models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'


class PublicUserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = (
            'id',
            'picture',
            'nickname',

            'user'
        )


class UserProfileUpdateActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = (
            'see_sexual',
            'see_social',
            'nickname',
            'picture',
        )
