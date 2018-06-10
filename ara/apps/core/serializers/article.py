from rest_framework import serializers

from apps.core.models import Article, ArticleReadLog, ArticleUpdateLog, Report, Vote
from apps.core.serializers.article_log import ArticleUpdateLogSerializer
from apps.core.serializers.board import BoardSerializer
from apps.core.serializers.comment import CommentSerializer
from apps.core.serializers.topic import TopicSerializer
from apps.core.serializers.report import ReportSerializer


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = '__all__'

    parent_topic = TopicSerializer()
    parent_board = BoardSerializer()

    created_by = serializers.SerializerMethodField()
    read_status = serializers.SerializerMethodField()

    def get_created_by(self, obj):
        if obj.is_anonymous:
            return '익명'

        return obj.created_by.profile.nickname

    def get_read_status(self, obj):
        user = self.context['request'].user

        try:
            article_read_log = ArticleReadLog.objects.get(
                article=obj,
                read_by=user
            )

        except ArticleReadLog.DoesNotExist:
            return 'N'

        last_article_update_log = ArticleUpdateLog.objects.order_by('created_at').filter(
            article=obj,
        ).last()

        if last_article_update_log:
            if last_article_update_log.created_at > article_read_log.last_read_at:
                return 'U'

        if obj.commented_at:
            if obj.commented_at > article_read_log.last_read_at:
                return 'U'

        return '-'


class ArticleDetailActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = '__all__'

    my_vote = serializers.SerializerMethodField()
    my_report = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()
    article_current_page = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    read_status = serializers.SerializerMethodField()

    parent_topic = TopicSerializer()
    parent_board = BoardSerializer()
    article_update_logs = ArticleUpdateLogSerializer(
        many=True,
        source='article_update_log_set',
    )

    list_serializer_class = ArticleSerializer

    def get_created_by(self, obj):
        if obj.is_anonymous:
            return '익명'

        return obj.created_by.profile.nickname

    def get_my_vote(self, obj):

        try:
            return obj.vote_set.get(
                created_by=self.context['request'].user,
            ).is_positive

        except Vote.DoesNotExist:
            return None

    def get_my_report(self, obj):

        try:
            return ReportSerializer(
                instance=obj.report_set.get(
                    reported_by=self.context['request'].user,
                ),
            ).data

        except Report.DoesNotExist:
            return None

    def get_comments(self, obj):
        return CommentSerializer(
            obj.comment_set.all(), many=True,
            **{'context': {'request': self.context.get('request')}}
        ).data

    def get_article_current_page(self, obj):
        view = self.context.get('view')

        paginator = view.paginator.django_paginator_class(view.filter_queryset(view.get_queryset()), view.paginator.page_size)

        for page_number in paginator.page_range:
            page = paginator.page(page_number)

            if obj.id in [object.id for object in page.object_list]:
                return page_number

    def get_read_status(self, obj):
        user = self.context['request'].user

        try:
            article_read_log = ArticleReadLog.objects.get(
                article=obj,
                read_by=user
            )

        except ArticleReadLog.DoesNotExist:
            return 'N'

        last_article_update_log = ArticleUpdateLog.objects.order_by('created_at').filter(
            article=obj,
        ).last()

        if last_article_update_log:
            if last_article_update_log.created_at > article_read_log.last_read_at:
                return 'U'

        if obj.commented_at:
            if obj.commented_at > article_read_log.last_read_at:
                return 'U'

        return '-'


class ArticleCreateActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
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


class ArticleUpdateActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
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
