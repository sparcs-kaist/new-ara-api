from ara.classes.serializers import MetaDataModelSerializer

from apps.core.models.communication_article import CommunicationArticle


class CommunicationArticleSerializer(MetaDataModelSerializer):
    class Meta:
        model = CommunicationArticle
        fields = '__all__'

    # TODO: is_confirmed_by_school 등을 timestamp 말고 progress_statues enum으로 바꿔서 프론트 보내주기
    # 좋아요 30개 달설 전, 달성 후 확인 전, 확인 후 답변전, 답변 완료

# class CommunicationArticleSerializer(BaseCommunicationArticleSerializer):
#     class Meta(BaseCommunicationArticleSerializer.Meta):


class CommunicationArticleUpdateActionSerializer(CommunicationArticleSerializer):
    class Meta(CommunicationArticleSerializer.Meta):
        read_only_fields = (
            'article',
            'response_deadline',
            'answered_at',
            'school_response_status'
        )
