from rest_framework import serializers

from apps.core.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'

    is_read = serializers.SerializerMethodField()

    from apps.core.serializers.article import BaseArticleSerializer
    related_article = BaseArticleSerializer()

    from apps.core.serializers.comment import BaseCommentSerializer
    related_comment = BaseCommentSerializer()

    def get_is_read(self, obj):
        return obj.notification_read_log_set.get(
            read_by=self.context['request'].user,
        ).is_read
