from django.contrib import admin

from apps.meal.models import MenuPhoto


@admin.register(MenuPhoto)
class MenuPhotoAdmin(admin.ModelAdmin):
    list_display = ("id", "restaurant", "date", "meal_time", "created_by", "source", "created_at")
    list_filter = ("restaurant", "meal_time", "source")
    search_fields = ("comment",)
