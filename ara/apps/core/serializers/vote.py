from rest_framework import serializers

from ara.classes.serializers import MetaDataModelSerializer

from apps.core.models import Vote


class VoteCreateActionSerializer(MetaDataModelSerializer):
    class Meta:
        model = Vote
        fields = (
            'parent_article',
            'parent_comment',
            'is_positive',
        )


class VoteUpdateActionSerializer(MetaDataModelSerializer):
    class Meta:
        model = Vote
        fields = (
            'is_positive',
        )
