from django.contrib import admin

from apps.meal.models import MenuPhoto, Restaurant


@admin.register(MenuPhoto)
class MenuPhotoAdmin(admin.ModelAdmin):
    list_display = ("id", "restaurant", "date", "meal_time", "created_by", "source", "created_at")
    list_filter = ("restaurant", "meal_time", "source")
    search_fields = ("comment",)


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ("id", "restaurant_name", "code", "is_active")
    list_filter = ("is_active",)
    list_editable = ("is_active",)
