from django.contrib import admin

from ara.classes.admin import MetaDataModelAdmin

from apps.core.models import Board, Topic, Article, \
    ArticleReadLog, ArticleDeleteLog, BestArticle, CommentDeleteLog, BestComment, FAQ, BestSearch, Report, Comment


@admin.register(Board)
class BoardAdmin(MetaDataModelAdmin):
    list_display = (
        'ko_name',
        'en_name',
        'is_readonly',
        'is_hidden',
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
        'parent_board',
    )
    search_fields = (
        'ko_name',
        'en_name',
        'ko_description',
        'en_description',
    )
    list_filter = (
        'parent_board',
    )


@admin.register(FAQ)
class FAQAdmin(MetaDataModelAdmin):
    list_display = (
        'ko_question',
        'en_question',
        'ko_answer',
        'en_answer',
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
    )


@admin.register(Comment)
class CommentAdmin(MetaDataModelAdmin):
    list_filter = (
        'is_anonymous',
    )
    list_display = (
        'content',
        'positive_vote_count',
        'negative_vote_count',
        'is_anonymous',
        'created_by',
        'parent_article',
        'parent_comment',
    )
    search_fields = (
        'content',
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


@admin.register(ArticleDeleteLog)
class ArticleDeleteLogAdmin(MetaDataModelAdmin):
    list_filter = (
        'article',
    )
    list_display = (
        'deleted_by',
        'article',
        'created_at',
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
        'created_at',
    )
    search_fields = (
        'deleted_by__username',
    )


@admin.register(BestComment)
class BestCommentAdmin(MetaDataModelAdmin):
    pass


@admin.register(BestSearch)
class BestSearchAdmin(MetaDataModelAdmin):
    list_display = (
        'ko_word',
        'en_word',
        'registered_by',
        'latest',
    )
    search_fields = (
        'ko_word',
        'en_word',
    )


@admin.register(Report)
class ReportAdmin(MetaDataModelAdmin):
    list_display = (
        'parent_article',
        'parent_comment',
        'reported_by',
        'type',
        'content',
    )
