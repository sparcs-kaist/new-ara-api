from rest_framework import serializers

from apps.course.models import Course, Professor


class ProfessorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Professor
        fields = ("id", "name")


class CourseSerializer(serializers.ModelSerializer):
    professors = ProfessorSerializer(many=True, read_only=True)
    enrollment_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Course
        fields = (
            "id",
            "course_code",
            "title",
            "department_name",
            "year",
            "semester",
            "credit",
            "professors",
            "enrollment_count",
            "last_synced_at",
        )
        read_only_fields = fields
