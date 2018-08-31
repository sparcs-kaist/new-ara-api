from rest_framework import serializers

from apps.core.models import Notification


class BaseNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'

    def get_is_read(self, obj):
        if not obj.notification_read_log_set.exists():
            return None

        my_notification_read_log = obj.notification_read_log_set.all()[0]

        return my_notification_read_log.is_read


class NotificationSerializer(BaseNotificationSerializer):
    is_read = serializers.SerializerMethodField()

    from apps.core.serializers.article import BaseArticleSerializer
    related_article = BaseArticleSerializer()

    from apps.core.serializers.comment import BaseCommentSerializer
    related_comment = BaseCommentSerializer()
