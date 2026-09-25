from rest_framework import serializers

from apps.user.models import UserNotificationPreference


class UserNotificationPreferenceSerializer(serializers.ModelSerializer):
    # 함께 배달 소식을 끌 때 안내를 확인했다는 표시
    confirm_delivery_off = serializers.BooleanField(write_only=True, required=False, default=False)

    class Meta:
        model = UserNotificationPreference
        fields = ["article_commented", "comment_commented", "chat_message", "delivery", "confirm_delivery_off"]

    def update(self, instance, validated_data):
        validated_data.pop("confirm_delivery_off", None)
        return super().update(instance, validated_data)
