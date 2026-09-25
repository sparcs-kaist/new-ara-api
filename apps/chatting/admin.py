from django.contrib import admin

from apps.chatting.models import ChatReport


@admin.register(ChatReport)
class ChatReportAdmin(admin.ModelAdmin):
    list_display = (
        "id", "chat_room", "reported_anon_number", "type",
        "reporter_email", "reported_email", "message_preview", "created_at",
    )
    list_filter = ("type",)
    search_fields = ("reporter_email", "reported_email", "content")
    list_select_related = ("chat_room", "message")

    @admin.display(description="메시지")
    def message_preview(self, obj):
        return obj.message.message_content[:50] if obj.message else ""
