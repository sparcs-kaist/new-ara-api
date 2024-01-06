from django.contrib import admin

from ara.classes.admin import MetaDataModelAdmin

from .models import GlobalNotice


@admin.register(GlobalNotice)
class GlobalNoticeAdmin(MetaDataModelAdmin):
    list_display = ("ko_title", "en_title", "started_at", "expired_at")
    fields = (
        ("ko_title", "ko_content"),
        ("en_title", "en_content"),
        ("started_at", "expired_at"),
    )
