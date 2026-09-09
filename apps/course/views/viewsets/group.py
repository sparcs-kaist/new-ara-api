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

        # 각 Course의 active enrollment count를 annotate한다.
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

        # Active enrollment의 group만 조회하고 annotated courses를 prefetch해 N+1을 막는다.
        # `CourseEnrollment.objects`를 사용해 soft-deleted enrollment를 제외한다.
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
