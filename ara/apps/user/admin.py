from django.contrib import admin

from ara.classes.admin import MetaDataModelAdmin

from apps.user.models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(MetaDataModelAdmin):
    list_display = (
        'user',
        'sid',
    )
