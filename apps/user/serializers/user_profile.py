from ara.classes.serializers import MetaDataModelSerializer
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from rest_framework import serializers

from apps.user.models import UserProfile


class BaseUserProfileSerializer(MetaDataModelSerializer):
    email = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = '__all__'

    def get_email(self, obj):
        return obj.user.email


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
        nickname_changed = self.instance and value != self.instance.nickname
        if nickname_changed and not self.instance.can_change_nickname():
            next_change_date = self.instance.nickname_updated_at + relativedelta(months=3)
            raise serializers.ValidationError(f'닉네임은 3개월마다 변경 가능합니다. ({next_change_date.strftime("%Y/%m/%d")}부터 가능)')
        return value

    def update(self, instance, validated_data):
        new_nickname = validated_data.get('nickname')
        old_nickname = instance.nickname if instance else None
        if instance and new_nickname and old_nickname != new_nickname:
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
