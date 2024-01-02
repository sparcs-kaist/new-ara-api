from django.contrib import admin

from apps.global_notice.models import GlobalNotice
from ara.classes.admin import MetaDataModelAdmin


@admin.register(GlobalNotice)
class GlobalNoticeAdmin(MetaDataModelAdmin):
    list_display = ("ko_title", "en_title", "started_at", "expired_at")
    fields = (
        ("ko_title", "ko_content"),
        ("en_title", "en_content"),
        ("started_at", "expired_at"),
    )
