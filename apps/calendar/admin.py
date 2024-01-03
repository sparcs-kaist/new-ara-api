from django.contrib import admin

from ara.classes.admin import MetaDataModelAdmin

from .models import Event, Tag


@admin.register(Event)
class EventAdmin(MetaDataModelAdmin):
    list_display = (
        "ko_title",
        "en_title",
        "is_all_day",
        "start_at",
        "end_at",
        "location",
        "url",
    )
    fields = (
        ("ko_title", "ko_description"),
        ("en_title", "en_description"),
        ("start_at", "end_at"),
        "is_all_day",
        "location",
        "url",
        "tags",
    )
    filter_horizontal = ("tags",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        "colored_ko_name",
        "en_name",
        "color",
    )
