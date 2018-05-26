from django.contrib import admin

from apps.session.models import UserProfile, OldAraUser
from ara.classes.admin import MetaDataModelAdmin


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
