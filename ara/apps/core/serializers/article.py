from rest_framework import serializers

from apps.core.models import Article
from apps.core.serializers.article_log import ArticleUpdateLogSerializer
from apps.core.serializers.board import BoardSerializer
from apps.core.serializers.comment import Depth1CommentSerializer
from apps.core.serializers.topic import TopicSerializer
from apps.core.serializers.report import ReportSerializer


class BaseArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article

    def get_my_vote(self, obj):
        if not obj.vote_set.exists():
            return None

        my_vote = obj.vote_set.all()[0]

        return my_vote.is_positive

    def get_my_report(self, obj):
        if not obj.report_set.exists():
            return None

        my_report = obj.report_set.all()[0]

        return ReportSerializer(my_report).data

    def get_created_by(self, obj):
        if obj.is_anonymous:
            return '익명'

        return obj.created_by.profile.nickname

    def get_read_status(self, obj):
        if not obj.article_read_log_set.exists():
            return 'N'

        my_article_read_log = obj.article_read_log_set.all()[0]

        # compare with article's last commented datetime
        if obj.commented_at:
            if obj.commented_at > my_article_read_log.last_read_at:
                return 'U'

        # compare with article's last updated datetime
        if obj.article_update_log_set.exists():
            last_article_update_log = obj.article_update_log_set.all()[0]

            if last_article_update_log.created_at > my_article_read_log.last_read_at:
                return 'U'

        return '-'

    # TODO: article_current_page property must be cached
    def get_article_current_page(self, obj):
        view = self.context.get('view')

        paginator = view.paginator.django_paginator_class(view.filter_queryset(view.get_queryset()), view.paginator.page_size)

        for page_number in paginator.page_range:
            page = paginator.page(page_number)

            if obj.id in [obj.id for obj in page.object_list]:
                return page_number


class ArticleSerializer(BaseArticleSerializer):
    class Meta(BaseArticleSerializer.Meta):
        fields = '__all__'

    parent_topic = TopicSerializer(
        read_only=True,
    )
    parent_board = BoardSerializer(
        read_only=True,
    )
    comments = Depth1CommentSerializer(
        many=True,
        read_only=True,
        source='comment_set',
    )
    article_update_logs = ArticleUpdateLogSerializer(
        many=True,
        read_only=True,
        source='article_update_log_set',
    )

    my_vote = serializers.SerializerMethodField(
        read_only=True,
    )
    my_report = serializers.SerializerMethodField(
        read_only=True,
    )
    created_by = serializers.SerializerMethodField(
        read_only=True,
    )
    read_status = serializers.SerializerMethodField(
        read_only=True,
    )
    article_current_page = serializers.SerializerMethodField(
        read_only=True,
    )
    

class ArticleListActionSerializer(BaseArticleSerializer):
    class Meta(BaseArticleSerializer.Meta):
        exclude = (
            'attachments',
        )

    parent_topic = TopicSerializer(
        read_only=True,
    )
    parent_board = BoardSerializer(
        read_only=True,
    )

    created_by = serializers.SerializerMethodField(
        read_only=True,
    )
    read_status = serializers.SerializerMethodField(
        read_only=True,
    )


class ArticleCreateActionSerializer(BaseArticleSerializer):
    class Meta(BaseArticleSerializer.Meta):
        fields = '__all__'
        read_only_fields = (
            'hit_count',
            'positive_vote_count',
            'negative_vote_count',
            'created_by',
            'created_at',
            'updated_at',
            'deleted_at',
            'commented_at',
        )


class ArticleUpdateActionSerializer(BaseArticleSerializer):
    class Meta(BaseArticleSerializer.Meta):
        fields = '__all__'
        read_only_fields = (
            'is_anonymous',
            'use_signature',
            'hit_count',
            'positive_vote_count',
            'negative_vote_count',
            'created_by',
            'parent_topic',
            'parent_board',
            'created_at',
            'updated_at',
            'deleted_at',
            'commented_at',
        )
