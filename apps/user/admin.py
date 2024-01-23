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
class UserGroupAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "nickname",
        "email",
        "group",
    )
    list_filter = ("group",)
    search_fields = (
        "user__id",
        "user__profile__nickname",
        "user__email",
    )

    @admin.display(description="닉네임")
    def nickname(self, obj: UserGroup):
        return obj.user.profile.nickname

    @admin.display(description="이메일")
    def email(self, obj: UserGroup):
        return obj.user.email


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "description",
        "is_official",
    )
    search_fields = ("name",)
