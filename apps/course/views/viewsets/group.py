"""CourseGroup (학기 무관 누적 과목 그룹) ViewSet.

엔드포인트:
- GET /api/course-groups/        — 본인이 수강한 과목들의 그룹 목록
- GET /api/course-groups/<pk>/   — 단일 그룹 상세

권한: 인증 필수, 본인이 enroll 된 Course 가 하나라도 속한 그룹만 노출.
"""

from __future__ import annotations

from django.db.models import Count, OuterRef, Prefetch, Subquery
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, permissions, viewsets

from apps.course.models import Course, CourseEnrollment, CourseGroup
from apps.course.serializers import CourseGroupSerializer


@extend_schema_view(
    list=extend_schema(tags=["course"], summary="본인 수강 과목 그룹 목록"),
    retrieve=extend_schema(tags=["course"], summary="과목 그룹 단건 조회"),
)
class CourseGroupViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = CourseGroupSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = None

    def get_queryset(self):
        user = self.request.user

        # 그룹 안 각 Course 의 active 수강 인원. CourseViewSet 과 동일 패턴.
        enrollment_count_subquery = Subquery(
            CourseEnrollment.objects
            .filter(course=OuterRef("pk"))
            .values("course")
            .annotate(count=Count("id"))
            .values("count")[:1]
        )
        courses_qs = (
            Course.objects
            .annotate(enrollment_count=enrollment_count_subquery)
            .prefetch_related("professors")
            .order_by("-year", "-semester")
        )

        # 본인이 enroll 된 Course 가 하나라도 속한 그룹만. courses 는 annotate 된
        # 쿼리셋으로 prefetch 해 serializer 가 N+1 없이 학기 목록을 만든다.
        #
        # enrollment 를 매니저(CourseEnrollment.objects) 경유로 먼저 필터해야
        # soft-delete(드랍) 된 수강이 빠진다. courses__enrollments 스패닝 JOIN 은
        # 관련 모델의 MetaDataManager 를 우회해 드랍한 수강도 매칭하므로 쓰지 않는다.
        enrolled_group_ids = (
            CourseEnrollment.objects
            .filter(user=user)
            .values("course__group_id")
        )
        return (
            CourseGroup.objects
            .filter(id__in=enrolled_group_ids)
            .distinct()
            .prefetch_related(Prefetch("courses", queryset=courses_qs))
            .order_by("course_code")
        )