from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.course.models import Course, CourseGroup, Professor


class ProfessorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Professor
        fields = ("id", "name")


class CourseSerializer(serializers.ModelSerializer):
    professors = ProfessorSerializer(many=True, read_only=True)
    otl_lecture_ids = serializers.ListField(
        child=serializers.IntegerField(), read_only=True
    )
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
            "otl_lecture_ids",
            "enrollment_count",
            "last_synced_at",
        )
        read_only_fields = fields


class OfferedTermSerializer(serializers.Serializer):
    """`CourseGroupSerializer.offered_terms` 항목의 schema 정의용.
    (Swagger에 offered_terms의 type이 string으로 표시되었었음)
    """

    course_id = serializers.IntegerField()
    year = serializers.IntegerField()
    semester = serializers.IntegerField()
    otl_lecture_ids = serializers.ListField(child=serializers.IntegerField())
    enrollment_count = serializers.IntegerField(allow_null=True)


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
        # `COURSE_CODE` group은 모든 Course의 professors를 prefetch 결과에서 deduplicate한다.
        courses = list(obj.courses.all())
        professors_by_id = {
            professor.id: professor
            for course in courses
            for professor in course.professors.all()
        }
        professors = sorted(professors_by_id.values(), key=lambda professor: professor.id)
        return ProfessorSerializer(professors, many=True).data

    @extend_schema_field(OfferedTermSerializer(many=True))
    def get_offered_terms(self, obj):
        return [
            {
                "course_id": course.id,
                "year": course.year,
                "semester": course.semester,
                "otl_lecture_ids": course.otl_lecture_ids,
                "enrollment_count": getattr(course, "enrollment_count", None),
            }
            for course in obj.courses.all()
        ]
