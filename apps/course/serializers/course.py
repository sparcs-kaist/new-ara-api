from rest_framework import serializers

from apps.course.models import Course, CourseGroup, Professor


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


class CourseGroupSerializer(serializers.ModelSerializer):
    """학기/연도 무관 누적 그룹. 겹치는 정보(코드/제목/교수)는 그룹 레벨에
    한 번만 두고, 학기마다 달라지는 값만 offered_terms 로 펼친다.

    뷰셋에서 group.courses 를 enrollment_count annotate + professors prefetch
    한 상태로 넘겨받는 것을 전제로 한다.
    """

    professors = serializers.SerializerMethodField()
    offered_terms = serializers.SerializerMethodField()

    class Meta:
        model = CourseGroup
        fields = ("id", "course_code", "title", "professors", "offered_terms")
        read_only_fields = fields

    def get_professors(self, obj):
        # 그룹 내 모든 Course 는 professors_key 가 같아 교수 집합이 동일.
        # 대표로 첫 Course 의 교수를 노출 (prefetch 된 것 재사용).
        courses = list(obj.courses.all())
        if not courses:
            return []
        return ProfessorSerializer(courses[0].professors.all(), many=True).data

    def get_offered_terms(self, obj):
        return [
            {
                "course_id": course.id,
                "year": course.year,
                "semester": course.semester,
                "enrollment_count": getattr(course, "enrollment_count", None),
            }
            for course in obj.courses.all()
        ]
