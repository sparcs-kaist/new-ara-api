from django.contrib import admin

from ara.classes.admin import MetaDataModelAdmin

from apps.core.models import Board, Topic, Article, \
        ArticleReadLog, ArticleUpdateLog, ArticleDeleteLog, BestArticle, CommentDeleteLog, BestComment


@admin.register(Board)
class BoardAdmin(MetaDataModelAdmin):
    list_display = (
        'ko_name',
        'en_name',
    )
    search_fields = (
        'ko_name',
        'en_name',
        'ko_description',
        'en_description',
    )


@admin.register(Topic)
class TopicAdmin(MetaDataModelAdmin):
    list_display = (
        'ko_name',
        'en_name',
    )
    search_fields = (
        'ko_name',
        'en_name',
        'ko_description',
        'en_description',
    )


@admin.register(Article)
class ArticleAdmin(MetaDataModelAdmin):
    list_filter = (
        'is_anonymous',
        'is_content_sexual',
        'is_content_social',
        'parent_topic',
        'parent_board',
    )
    list_display = (
        'title',
        'hit_count',
        'positive_vote_count',
        'negative_vote_count',
        'is_anonymous',
        'is_content_sexual',
        'is_content_social',
        'created_by',
        'parent_topic',
        'parent_board',
    )
    search_fields = (
        'title',
        'content',
        'ko_description',
        'en_description',
    )


@admin.register(ArticleReadLog)
class ArticleReadLogAdmin(MetaDataModelAdmin):
    list_filter = (
        'article',
    )
    list_display = (
        'read_by',
        'article',
        'created_at',
    )
    search_fields = (
        'read_by__username',
    )


@admin.register(ArticleUpdateLog)
class ArticleUpdateLogAdmin(MetaDataModelAdmin):
    list_filter = (
        'is_content_sexual',
        'is_content_social',
        'parent_topic',
        'parent_board',
    )
    list_display = (
        'updated_by',
        'article',
        'is_content_sexual',
        'is_content_social',
        'use_signature',
        'parent_topic',
        'parent_board',
    )
    search_fields = (
        'updated_by__username',
    )

@admin.register(ArticleDeleteLog)
class ArticleDeleteLogAdmin(MetaDataModelAdmin):
    list_filter = (
        'article',
    )
    list_display = (
        'deleted_by',
        'article',
        'deleted_time',
    )
    search_fields = (
        'deleted_by__username',
    )

@admin.register(BestArticle)
class BestArticleAdmin(MetaDataModelAdmin):
    pass


@admin.register(CommentDeleteLog)
class CommentDeleteLogAdmin(MetaDataModelAdmin):
    list_filter = (
        'comment',
    )
    list_display = (
        'deleted_by',
        'comment',
        'deleted_time',
    )
    search_fields = (
        'deleted_by__username',
    )

@admin.register(BestComment)
class BestCommentAdmin(MetaDataModelAdmin):
    pass
