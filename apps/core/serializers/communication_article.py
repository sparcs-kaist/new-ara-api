import sys

from django.utils import timezone
from rest_framework import serializers

from ara.classes.serializers import MetaDataModelSerializer
from apps.core.models.communication_article import CommunicationArticle


class BaseCommunicationArticleSerializer(MetaDataModelSerializer):
    class Meta:
        model = CommunicationArticle
        fields = '__all__'
        read_only_fields = (
            'article',
            'response_deadline',
            'answered_at',
            'school_response_status',
        )


class CommunicationArticleSerializer(BaseCommunicationArticleSerializer):
    days_left = serializers.SerializerMethodField(
        read_only=True,
    )

    @staticmethod
    def get_days_left(obj) -> int:
        if obj.response_deadline == timezone.datetime.min.replace(tzinfo=timezone.utc):
            return sys.maxsize
        else:
            return (obj.response_deadline.astimezone(timezone.localtime().tzinfo) - timezone.localtime()).days


class CommunicationArticleUpdateActionSerializer(BaseCommunicationArticleSerializer):
    class Meta(BaseCommunicationArticleSerializer.Meta):
        pass
