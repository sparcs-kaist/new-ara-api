from ara.classes.serializers import MetaDataModelSerializer

from apps.core.models import Vote


class BaseVoteSerializer(MetaDataModelSerializer):
    class Meta:
        model = Vote
        fields = '__all__'


class VoteSerializer(BaseVoteSerializer):
    pass


class VoteCreateActionSerializer(BaseVoteSerializer):
    class Meta(BaseVoteSerializer.Meta):
        read_only_fields = (
            'voted_by',
        )


class VoteUpdateActionSerializer(BaseVoteSerializer):
    class Meta(BaseVoteSerializer.Meta):
        read_only_fields = (
            'voted_by'
            'parent_article',
            'parent_comment',
        )
