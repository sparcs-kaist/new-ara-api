from rest_framework import serializers

from ara.classes.serializers import MetaDataModelSerializer

from apps.core.models.communication_article import CommunicationArticle


class CommunicationArticleSerializer(MetaDataModelSerializer):
    positive_vote_count = serializers.IntegerField(source='article.positive_vote_count')

    class Meta:
        model = CommunicationArticle
        fields = '__all__'
