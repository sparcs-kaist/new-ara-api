from django.contrib import admin

from apps.course.grouping import regroup_existing_courses
from apps.course.models import CourseGroup, CourseGroupingRule


@admin.register(CourseGroupingRule)
class CourseGroupingRuleAdmin(admin.ModelAdmin):
    list_display = (
        "course_code",
        "strategy",
        "is_active",
        "updated_at",
    )
    list_filter = ("strategy", "is_active")
    search_fields = ("course_code", "description")
    readonly_fields = ("created_at", "updated_at")

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        regroup_existing_courses(obj.course_code)

    def delete_model(self, request, obj):
        course_code = obj.course_code
        super().delete_model(request, obj)
        regroup_existing_courses(course_code)

    def delete_queryset(self, request, queryset):
        course_codes = list(queryset.values_list("course_code", flat=True))
        super().delete_queryset(request, queryset)
        for course_code in course_codes:
            regroup_existing_courses(course_code)


@admin.register(CourseGroup)
class CourseGroupAdmin(admin.ModelAdmin):
    """규칙 적용 결과 확인용. 그룹 자체는 sync와 규칙 서비스가 관리한다."""

    list_display = (
        "course_code",
        "title",
        "professors_key",
        "title_year",
        "title_semester",
    )
    search_fields = ("course_code", "title", "professors_key")
    readonly_fields = (
        "course_code",
        "title",
        "professors_key",
        "title_year",
        "title_semester",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
