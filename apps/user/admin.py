from django.contrib import admin

from ara.classes.admin import MetaDataModelAdmin

from apps.user.models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(MetaDataModelAdmin):
    list_filter = (
        'see_sexual',
        'see_social',
        'group',
        'is_newara',
    )
    list_display = (
        'uid',
        'sid',
        'nickname',
        'user',
        'group',
    )
    search_fields = (
        'uid',
        'sid',
        'nickname',
        'user',
    )
