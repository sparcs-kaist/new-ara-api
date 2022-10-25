from django.contrib import admin
from django.utils.translation import gettext
from django.utils import timezone

from ara.classes.admin import MetaDataModelAdmin

from apps.core.models import (
    Board,
    Topic,
    Article,
    ArticleReadLog,
    ArticleDeleteLog,
    BestArticle,
    CommentDeleteLog,
    BestComment,
    FAQ,
    BestSearch,
    Report,
    Comment,
    CommunicationArticle,
)
from ara.settings import MIN_TIME


class HiddenContentListFilter(admin.SimpleListFilter):
    title = gettext("Hidden Contents")
    parameter_name = "hidden_at"

    def lookups(self, request, model_admin):
        return (
            ("hidden", "예"),
            ("not_hidden", "아니오"),
        )

    def queryset(self, request, queryset):
        if self.value() == "hidden":
            return queryset.exclude(hidden_at=MIN_TIME)
        if self.value() == "not_hidden":
            return queryset.filter(hidden_at=MIN_TIME)


@admin.register(Board)
class BoardAdmin(MetaDataModelAdmin):
    list_display = (
        "ko_name",
        "en_name",
        "is_readonly",
        "is_hidden",
    )
    search_fields = (
        "ko_name",
        "en_name",
        "ko_description",
        "en_description",
    )


@admin.register(Topic)
class TopicAdmin(MetaDataModelAdmin):
    list_display = (
        "ko_name",
        "en_name",
        "parent_board",
    )
    search_fields = (
        "ko_name",
        "en_name",
        "ko_description",
        "en_description",
    )
    list_filter = ("parent_board",)


@admin.register(FAQ)
class FAQAdmin(MetaDataModelAdmin):
    list_display = (
        "ko_question",
        "en_question",
        "ko_answer",
        "en_answer",
    )


@admin.register(Article)
class ArticleAdmin(MetaDataModelAdmin):
    list_filter = (
        "name_type",
        "is_content_sexual",
        "is_content_social",
        "parent_topic",
        "parent_board",
        HiddenContentListFilter,
    )
    list_display = (
        "title",
        "hit_count",
        "positive_vote_count",
        "negative_vote_count",
        "name_type",
        "is_content_sexual",
        "is_content_social",
        "report_count",
        "hidden_at",
    )
    raw_id_fields = (
        "created_by",
        "parent_topic",
        "parent_board",
    )
    search_fields = ("title", "content", "hidden_at", "created_by__email")
    actions = ("restore_hidden_articles",)

    @admin.action(description=gettext("Restore hidden articles"))
    def restore_hidden_articles(self, request, queryset):
        rows_updated = queryset.update(hidden_at=MIN_TIME)
        self.message_user(request, f"{rows_updated}개의 게시물(들)이 성공적으로 복구되었습니다.")


@admin.register(Comment)
class CommentAdmin(MetaDataModelAdmin):
    list_filter = (
        "name_type",
        HiddenContentListFilter,
    )
    list_display = (
        "content",
        "positive_vote_count",
        "negative_vote_count",
        "name_type",
        "report_count",
        "hidden_at",
    )
    raw_id_fields = (
        "created_by",
        "parent_article",
        "parent_comment",
    )
    search_fields = ("content", "hidden_at", "created_by__email")
    actions = ("restore_hidden_comments",)

    @admin.action(description=gettext("Restore hidden comments"))
    def restore_hidden_comments(self, request, queryset):
        rows_updated = queryset.update(hidden_at=MIN_TIME)
        self.message_user(request, f"{rows_updated}개의 댓글(들)이 성공적으로 복구되었습니다.")


@admin.register(ArticleReadLog)
class ArticleReadLogAdmin(MetaDataModelAdmin):
    list_filter = ("article",)
    list_display = (
        "read_by",
        "article",
        "created_at",
    )
    search_fields = ("read_by__username",)


@admin.register(ArticleDeleteLog)
class ArticleDeleteLogAdmin(MetaDataModelAdmin):
    list_filter = ("article",)
    list_display = (
        "deleted_by",
        "article",
        "created_at",
    )
    search_fields = ("deleted_by__username",)


@admin.register(BestArticle)
class BestArticleAdmin(MetaDataModelAdmin):
    pass


@admin.register(CommentDeleteLog)
class CommentDeleteLogAdmin(MetaDataModelAdmin):
    list_filter = ("comment",)
    list_display = (
        "deleted_by",
        "comment",
        "created_at",
    )
    search_fields = ("deleted_by__username",)


@admin.register(BestComment)
class BestCommentAdmin(MetaDataModelAdmin):
    pass


@admin.register(BestSearch)
class BestSearchAdmin(MetaDataModelAdmin):
    list_display = (
        "ko_word",
        "en_word",
        "registered_by",
        "latest",
    )
    search_fields = (
        "ko_word",
        "en_word",
    )


@admin.register(Report)
class ReportAdmin(MetaDataModelAdmin):
    list_display = (
        "parent_article",
        "parent_comment",
        "reported_by",
        "type",
        "content",
    )


@admin.register(CommunicationArticle)
class CommunicationArticleAdmin(MetaDataModelAdmin):
    list_filter = (
        "response_deadline",
        "answered_at",
    )
    list_display = (
        "article",
        "get_status_string",
        "response_deadline",
        "answered_at",
    )
    raw_id_fields = ("article",)
