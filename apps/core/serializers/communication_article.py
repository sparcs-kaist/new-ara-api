from django.utils import timezone
from datetime import timedelta
from rest_framework import serializers

from ara.classes.serializers import MetaDataModelSerializer
from apps.core.models.communication_article import CommunicationArticle


class BaseCommunicationArticleSerializer(MetaDataModelSerializer):
    positive_vote_count = serializers.IntegerField(source='article.positive_vote_count')
    class Meta:
        model = CommunicationArticle
        fields = '__all__'


class CommunicationArticleSerializer(BaseCommunicationArticleSerializer):
    days_left = serializers.SerializerMethodField(
        read_only=True,
    )

    @staticmethod
    def get_days_left(obj) -> int:
        no_deadline = 30
        if obj.response_deadline == timezone.datetime.min.replace(tzinfo=timezone.utc):
            return no_deadline
        else:
            return ((obj.response_deadline + timedelta(hours=9)).date() - timezone.localtime().now().date()).days


class CommunicationArticleUpdateActionSerializer(BaseCommunicationArticleSerializer):
    class Meta(BaseCommunicationArticleSerializer.Meta):
        read_only_fields = (
            'article',
            'response_deadline',
            'answered_at',
            'school_response_status'
        )
