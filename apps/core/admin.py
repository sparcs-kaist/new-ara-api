from django.contrib import admin
from django.utils import timezone
from django.utils.translation import gettext

from apps.core.models import (
    FAQ,
    Article,
    ArticleDeleteLog,
    ArticleReadLog,
    BestArticle,
    BestComment,
    BestSearch,
    Board,
    BoardGroup,
    Comment,
    CommentDeleteLog,
    CommunicationArticle,
    Report,
    Topic,
)
from ara.classes.admin import MetaDataModelAdmin


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
            return queryset.exclude(hidden_at=None)
        if self.value() == "not_hidden":
            return queryset.filter(hidden_at=None)


@admin.register(Board)
class BoardAdmin(MetaDataModelAdmin):
    list_display = (
        "ko_name",
        "en_name",
        "group",
        "is_readonly",
        "is_hidden",
    )
    search_fields = (
        "ko_name",
        "en_name",
    )


@admin.register(BoardGroup)
class BoardGroupAdmin(admin.ModelAdmin):
    list_display = (
        "slug",
        "ko_name",
        "en_name",
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
    actions = ("restore_hidden_articles",)
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
        "parent_board",
        "user_nickname",
        "user_email",
        "hit_count",
        "report_count",
        "created_at",
        "hidden_at",
    )
    raw_id_fields = ("created_by",)
    search_fields = (
        "title",
        "content",
        "hidden_at",
        "created_by__email",
    )
    fields = (
        "title",
        "content",
        "created_by",
        "parent_board",
        "parent_topic",
        "name_type",
        ("is_content_sexual", "is_content_social"),
        ("hit_count", "migrated_hit_count"),
        ("positive_vote_count", "migrated_positive_vote_count"),
        ("negative_vote_count", "migrated_negative_vote_count"),
        ("comment_count", "report_count"),
        "attachments",
        "content_updated_at",
        "commented_at",
        "url",
        ("hidden_at", "topped_at"),
    )
    readonly_fields = (
        "hit_count",
        "positive_vote_count",
        "negative_vote_count",
        "comment_count",
        "report_count",
        "commented_at",
        "content_updated_at",
    )
    filter_horizontal = ("attachments",)

    @admin.action(description=gettext("Restore hidden articles"))
    def restore_hidden_articles(self, request, queryset):
        rows_updated = queryset.update(hidden_at=None)
        self.message_user(request, f"{rows_updated}개의 게시물(들)이 성공적으로 복구되었습니다.")

    @admin.display(description="닉네임")
    def user_nickname(self, obj: Article):
        return obj.created_by_nickname

    @admin.display(description="이메일")
    def user_email(self, obj: Article):
        return obj.created_by.email


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
        rows_updated = queryset.update(hidden_at=None)
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
        "target_type",
        "parent_article",
        "parent_comment",
        "chat_room",
        "reported_by",
        "reported_user",
        "reporter_email",
        "reported_email",
        "target_preview",
        "type",
        "content",
        "status",
        "handled_by",
        "status_changed_at",
    )
    list_filter = ("status", "type")
    search_fields = ("reporter_email", "reported_email", "content")
    list_select_related = (
        "parent_article", "parent_comment", "chat_room", "chat_message", "reported_by", "reported_user", "handled_by",
    )
    readonly_fields = ("handled_by", "status_changed_at")
    actions = ("mark_in_progress", "mark_done")

    def set_status(self, request, queryset, status):
        queryset.update(status=status, handled_by=request.user, status_changed_at=timezone.now())

    @admin.action(description="선택한 신고를 처리 중으로")
    def mark_in_progress(self, request, queryset):
        self.set_status(request, queryset, Report.STATUS_IN_PROGRESS)

    @admin.action(description="선택한 신고를 처리 완료로")
    def mark_done(self, request, queryset):
        self.set_status(request, queryset, Report.STATUS_DONE)

    # 상세 화면에서 상태를 바꿔도 처리자 / 시각을 남긴다
    def save_model(self, request, obj, form, change):
        if change and "status" in form.changed_data:
            obj.handled_by = request.user
            obj.status_changed_at = timezone.now()
        super().save_model(request, obj, form, change)

    @admin.display(description="대상")
    def target_preview(self, obj):
        if obj.parent_article:
            return obj.parent_article.title[:50]
        if obj.parent_comment:
            return obj.parent_comment.content[:50]
        if obj.chat_message:
            return obj.chat_message.message_content[:50]
        return ""


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
