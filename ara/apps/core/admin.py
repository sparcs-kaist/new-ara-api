from django.contrib import admin

from ara.classes.admin import MetaDataModelAdmin

from apps.core.models import Board


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
