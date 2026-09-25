from django.contrib import admin

from apps.meal.models import MenuPhoto


# 부적절한 메뉴 사진은 관리자가 여기서 지운다
@admin.register(MenuPhoto)
class MenuPhotoAdmin(admin.ModelAdmin):
    list_display = ("id", "restaurant", "date", "meal_time", "created_by", "source", "created_at")
    list_filter = ("restaurant", "meal_time", "source")
    search_fields = ("comment",)
