from rest_framework import serializers

from apps.core.models import Vote


class VoteCreateActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vote
        fields = (
            'parent_article',
            'parent_comment',
            'is_positive',
        )


class VoteUpdateActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vote
        fields = (
            'is_positive',
        )
