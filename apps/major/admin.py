from django.contrib import admin

from apps.major.models import Major


@admin.register(Major)
class MajorAdmin(admin.ModelAdmin):
    list_display = (
        "std_dept_id",
        "major_code",
        "major_name",
        "major_name_eng",
        "major_dept_location",
    )
    search_fields = ("major_code", "major_name", "major_name_eng")
