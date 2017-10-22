from rest_framework import serializers

from apps.core.models import Comment


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        exclude = (
            'parent_article',
            'parent_comment',

        )

    my_vote = serializers.SerializerMethodField()
    from apps.core.serializers.comment_log import CommentUpdateLogSerializer
    comment_update_log_set = CommentUpdateLogSerializer(
        many = True,
    )


    def get_my_vote(self, obj):
        from apps.core.models import Vote

        try:
            return obj.vote_set.get(
                created_by=self.context['request'].user,
            ).is_positive
        except:
            return None

        #except Vote.DoesNotExist:
        #    return None


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
