from django.contrib import admin

from apps.user.models import Group, UserGroup, UserProfile
from apps.user.models.user.manual import ManualUser
from ara.classes.admin import MetaDataModelAdmin


@admin.register(UserProfile)
class UserProfileAdmin(MetaDataModelAdmin):
    list_filter = (
        "see_sexual",
        "see_social",
        "is_newara",
    )
    list_display = (
        "uid",
        "sid",
        "nickname",
        "user",
    )
    search_fields = (
        "uid",
        "sid",
        "nickname",
        "user__id",
    )


@admin.register(ManualUser)
class ManualUserAdmin(MetaDataModelAdmin):
    list_display = (
        "user",
        "org_name",
        "org_type",
        "applicant_name",
        "sso_email",
    )


@admin.register(UserGroup)
class UserGroupAdmin(MetaDataModelAdmin):
    list_display = (
        "user_id",
        "group_id",
    )
    search_fields = (
        "user_id",
        "group_id",
    )


@admin.register(Group)
class GroupAdmin(MetaDataModelAdmin):
    list_display = (
        "group_id",
        "name",
        "is_official",
    )
    search_fields = (
        "id",
        "name",
    )
