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
        # COURSE_CODE 예외 그룹은 학기마다 교수가 다를 수 있으므로 그룹에 속한
        # 모든 Course의 교수를 중복 없이 합쳐서 노출한다 (prefetch 결과 재사용).
        courses = list(obj.courses.all())
        professors_by_id = {
            professor.id: professor
            for course in courses
            for professor in course.professors.all()
        }
        professors = sorted(professors_by_id.values(), key=lambda professor: professor.id)
        return ProfessorSerializer(professors, many=True).data

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
