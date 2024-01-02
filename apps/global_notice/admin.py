from django.contrib import admin

from apps.global_notice.models import GlobalNotice
from ara.classes.admin import MetaDataModelAdmin


@admin.register(GlobalNotice)
class FAQAdmin(MetaDataModelAdmin):
    list_display = ("title", "content", "started_at", "expired_at")
    search_fields = ("title", "content")
