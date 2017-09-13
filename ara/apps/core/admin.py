from django.contrib import admin

from ara.classes.admin import MetaDataModelAdmin

from apps.core.models import Board, Topic, Article


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
