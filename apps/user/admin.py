from django.contrib import admin

from apps.user.models import UserProfile
from apps.user.models.user.manual import ManualUser
from ara.classes.admin import MetaDataModelAdmin


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


@admin.register(ManualUser)
class ManualUserAdmin(MetaDataModelAdmin):
     list_display = (
         'user',
         'org_name',
         'org_type',
         'applicant_name',
         'sso_email',
     )
