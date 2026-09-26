from django.contrib import admin, messages
from django.utils.html import format_html

from apps.meal.models import MenuPhoto, Restaurant, Store, StoreEvent, StoreMenu, StoreNotice, StoreStaff
from apps.user.models import UserProfile


@admin.register(MenuPhoto)
class MenuPhotoAdmin(admin.ModelAdmin):
    list_display = ("id", "restaurant", "date", "meal_time", "created_by", "source", "created_at")
    list_filter = ("restaurant", "meal_time", "source")
    search_fields = ("comment",)


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ("id", "restaurant_name", "display_name", "code", "is_active")
    list_filter = ("is_active",)
    list_editable = ("display_name", "is_active")


class StoreStaffInline(admin.TabularInline):
    model = StoreStaff
    extra = 0
    autocomplete_fields = ("user",)
    fields = ("user",)


class StoreMenuInline(admin.TabularInline):
    model = StoreMenu
    extra = 0
    fields = ("order", "section", "name", "price", "description", "photo", "is_sold_out", "is_signature")


class StoreNoticeInline(admin.TabularInline):
    model = StoreNotice
    extra = 0
    fields = ("title", "body", "starts_at", "ends_at")


class StoreEventInline(admin.TabularInline):
    model = StoreEvent
    extra = 0
    fields = ("kind", "starts_at", "ends_at", "reason", "open_time", "close_time")


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "zone", "location", "is_active", "order", "cover_preview")
    list_filter = ("zone", "is_active")
    search_fields = ("name", "location")
    readonly_fields = ("cover_preview",)
    inlines = (StoreStaffInline, StoreMenuInline, StoreNoticeInline, StoreEventInline)

    @admin.display(description="대표 이미지")
    def cover_preview(self, obj):
        return format_html('<img src="{}" style="height: 60px">', obj.cover.url) if obj.cover else ""

    # 직원으로 지정한 계정이 입주업체 직원 그룹이 아니면 알린다 (그룹은 자동으로 바꾸지 않는다)
    def save_formset(self, request, form, formset, change):
        super().save_formset(request, form, formset, change)
        if formset.model is not StoreStaff:
            return
        for staff in form.instance.staff.select_related("user__profile"):
            profile = getattr(staff.user, "profile", None)
            if not profile or profile.group != UserProfile.UserGroup.STORE_EMPLOYEE:
                messages.warning(request, f"{staff.user} 계정은 입주업체 직원(STORE_EMPLOYEE) 그룹이 아니에요. 사용자 프로필에서 그룹을 확인해주세요.")
