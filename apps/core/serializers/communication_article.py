from ara.classes.serializers import MetaDataModelSerializer

from apps.core.models.communication_article import CommunicationArticle


class BaseCommunicationArticleSerializer(MetaDataModelSerializer):
    class Meta:
        model = CommunicationArticle
        fields = '__all__'


class CommunicationArticleSerializer(BaseCommunicationArticleSerializer):
    pass
