from rest_framework import serializers

from apps.core.models import Comment


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        exclude = (
            'parent_article',
            'parent_comment',

        )


class CommentCreateActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = (
            'content',
            'is_anonymous',
            'is_content_sexual',
            'is_content_social',
            'use_signature',
            'parent_article',
            'parent_comment',
            'attachment',
        )


class CommentUpdateActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = (
            'content',
            'is_content_sexual',
            'is_content_social',
            'attachment',
        )
