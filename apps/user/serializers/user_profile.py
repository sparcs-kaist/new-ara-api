from django.utils.translation import gettext

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

    @staticmethod
    def get_email(obj) -> str:
        if obj.email.endswith('@sso.sparcs.org'):
            return None
        return obj.email


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

    def validate_nickname(self, value) -> str:
        nickname_changed = self.instance and value != self.instance.nickname
        if nickname_changed and not self.instance.can_change_nickname():
            next_change_date = self.instance.nickname_updated_at + relativedelta(months=3)
            raise serializers.ValidationError(
                gettext('Nicknames can only be changed every 3 months. (can\'t change until %(date)s)')
                % {'date': next_change_date.strftime("%Y/%m/%d")}
            )
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
            'picture',
            'nickname',
            'user'
        )
