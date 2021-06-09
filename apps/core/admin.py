from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Q

from ara.classes.admin import MetaDataModelAdmin

from apps.core.models import Board, Topic, Article, \
    ArticleReadLog, ArticleDeleteLog, BestArticle, CommentDeleteLog, BestComment, FAQ, BestSearch, Report, Comment

class HiddenArticleListFilter(admin.SimpleListFilter):
    title = _('Hidden Article')
    parameter_name = 'hidden_at'

    def lookups(self, request, model_admin):
        return (
            ('1', _('숨김 처리된 글')),
        )

    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.exclude(hidden_at = timezone.datetime.min.replace(tzinfo=timezone.utc))

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
        HiddenArticleListFilter,
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
        'report_count',
        'hidden_at',
    )
    search_fields = (
        'title',
        'content',
        'hidden_at',
    )
    actions = (
        'restore_articles',
        'delete_articles'
    )

    # 기존 delete action 제거
    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    # hidden_at 값 초기화
    def restore_articles(self, request, queryset):
        rows_updated = queryset.update(hidden_at=timezone.datetime.min.replace(tzinfo=timezone.utc))
        if rows_updated == 1:
            message_bit = '1개의 게시물이'
        else:
            message_bit = f'{rows_updated}개의 게시물들이'
        self.message_user(request, f'{message_bit} 성공적으로 복구되었습니다.')

    # 게시글 삭제 시 댓글도 함께 삭제되도록 save함수 추가
    def delete_articles(self, request, queryset):
        num = 0
        for e in queryset.filter(deleted_at=timezone.datetime.min.replace(tzinfo=timezone.utc)):
            e.deleted_at = timezone.now()
            e.save()
            num += 1
        if num == 1:
            message_bit = '1개의 게시물이'
        else:
            message_bit = f'{num}개의 게시물들이'
        self.message_user(request, f'{message_bit}성공적으로 삭제되었습니다.')


@admin.register(Comment)
class CommentAdmin(MetaDataModelAdmin):
    list_filter = (
        'is_anonymous',
        HiddenArticleListFilter,
    )
    list_display = (
        'content',
        'positive_vote_count',
        'negative_vote_count',
        'is_anonymous',
        'created_by',
        'parent_article',
        'parent_comment',
        'report_count',
        'hidden_at',
    )
    search_fields = (
        'content',
        'hidden_at',
    )
    actions = (
        'restore_comments',
        'delete_comments'
    )

    # 기존 delete action 제거
    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    # hidden_at값 초기화
    def restore_comments(self, request, queryset):
        rows_updated = queryset.update(hidden_at=timezone.datetime.min.replace(tzinfo=timezone.utc))
        if rows_updated == 1:
            message_bit = '1개의 댓글이'
        else:
            message_bit = f'{rows_updated}개의 댓글들이'
        self.message_user(request, f'{message_bit}성공적으로 복구되었습니다.')

    # 댓글 삭제 시 하위 댓글도 함께 삭제되도록 save함수 추가
    def delete_comments(self, request, queryset):
        num = 0
        for e in queryset.filter(deleted_at=timezone.datetime.min.replace(tzinfo=timezone.utc)):
            e.deleted_at = timezone.now()
            e.save()
            num += 1
        if num == 1:
            message_bit = '1개의 댓글이'
        else:
            message_bit = f'{num}개의 댓글들이'
        self.message_user(request, f'{message_bit}성공적으로 삭제되었습니다.')


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
