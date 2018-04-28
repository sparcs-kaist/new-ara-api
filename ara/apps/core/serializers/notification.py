from rest_framework import serializers

from apps.core.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'

    is_read = serializers.SerializerMethodField()

    from apps.core.serializers.article import ArticleSerializer
    related_article = ArticleSerializer()

    from apps.core.serializers.comment import CommentSerializer
    related_comment = CommentSerializer()

    def get_is_read(self, obj):
        return obj.notification_read_log_set.get(
            read_by=self.context['request'].user,
        ).is_read
