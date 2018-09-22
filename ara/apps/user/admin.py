from django.contrib import admin

from ara.classes.admin import MetaDataModelAdmin

from apps.user.models import UserProfile, OldAraUser


@admin.register(UserProfile)
class UserProfileAdmin(MetaDataModelAdmin):
    list_display = (
        'user',
        'sid',
    )


@admin.register(OldAraUser)
class OldAraUserAdmin(MetaDataModelAdmin):
    list_display = (
        'username',
        'nickname',
    )
