from rest_framework import serializers, exceptions

from ara.classes.serializers import MetaDataModelSerializer

from apps.core.models import Comment, Block


class BaseCommentSerializer(MetaDataModelSerializer):
    class Meta:
        model = Comment
        exclude = ('attachment', )

    @staticmethod
    def get_my_vote(obj):
        if not obj.vote_set.exists():
            return None

        my_vote = obj.vote_set.all()[0]

        return my_vote.is_positive

    def get_is_hidden(self, obj):
        if self.validate_hidden(obj):
            return True

        return False

    def get_why_hidden(self, obj):
        errors = self.validate_hidden(obj)

        return [
            {
                'detail': error.detail,
            } for error in errors
        ]

    def get_content(self, obj):
        errors = self.validate_hidden(obj)

        if errors:
            return [error.detail for error in errors]

        return obj.content

    def get_hidden_content(self, obj):
        if self.validate_hidden(obj):
            return obj.content

        return ''

    @staticmethod
    def get_created_by(obj):
        from apps.user.serializers.user import PublicUserSerializer

        if obj.is_anonymous:
            return '익명'

        return PublicUserSerializer(obj.created_by).data

    def validate_hidden(self, obj):
        errors = []

        if Block.is_blocked(blocked_by=self.context['request'].user, user=obj.created_by):
            errors.append(exceptions.ValidationError('차단한 사용자의 게시물입니다.'))

        return errors


class CommentSerializer(BaseCommentSerializer):
    from apps.user.serializers.user import PublicUserSerializer
    created_by = PublicUserSerializer(
        read_only=True,
    )
    my_vote = serializers.SerializerMethodField(
        read_only=True,
    )
    is_hidden = serializers.SerializerMethodField(
        read_only=True,
    )
    why_hidden = serializers.SerializerMethodField(
        read_only=True,
    )
    content = serializers.SerializerMethodField(
        read_only=True,
    )
    hidden_content = serializers.SerializerMethodField(
        read_only=True,
    )
    created_by = serializers.SerializerMethodField(
        read_only=True,
    )


class CommentListActionSerializer(BaseCommentSerializer):
    from apps.user.serializers.user import PublicUserSerializer
    created_by = PublicUserSerializer(
        read_only=True,
    )
    my_vote = serializers.SerializerMethodField(
        read_only=True,
    )
    is_hidden = serializers.SerializerMethodField(
        read_only=True,
    )
    why_hidden = serializers.SerializerMethodField(
        read_only=True,
    )
    content = serializers.SerializerMethodField(
        read_only=True,
    )
    hidden_content = serializers.SerializerMethodField(
        read_only=True,
    )
    created_by = serializers.SerializerMethodField(
        read_only=True,
    )


class CommentNestedCommentListActionSerializer(CommentListActionSerializer):
    pass


class ArticleNestedCommentListActionSerializer(CommentListActionSerializer):
    comments = CommentNestedCommentListActionSerializer(
        many=True,
        read_only=True,
        source='comment_set',
    )


class CommentCreateActionSerializer(BaseCommentSerializer):
    class Meta(BaseCommentSerializer.Meta):
        read_only_fields = (
            'positive_vote_count',
            'negative_vote_count',
            'created_by',
        )

    from apps.user.serializers.user import PublicUserSerializer
    created_by = PublicUserSerializer(
        read_only=True,
    )


class CommentUpdateActionSerializer(BaseCommentSerializer):
    class Meta(BaseCommentSerializer.Meta):
        read_only_fields = (
            'is_anonymous',
            'positive_vote_count',
            'negative_vote_count',
            'created_by',
            'parent_article',
            'parent_comment',
        )

    from apps.user.serializers.user import PublicUserSerializer
    created_by = PublicUserSerializer(
        read_only=True,
    )
