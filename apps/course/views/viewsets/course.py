"""Course (과목게시판) ViewSet.

엔드포인트:
- GET  /api/courses/me/                 — 본인 수강 과목. 24h 캐시 만료 시 OTL sync
- GET  /api/courses/?year=&semester=    — 본인 수강 과목 중 학기 필터
- GET  /api/courses/<pk>/               — 단일 과목 상세 (enrollment 필수)

권한:
- 인증 필수
- 본인이 enroll 된 과목만 노출 (queryset 필터)
- 단일 retrieve 는 IsEnrolledInCourse 가 추가로 확인
"""

from __future__ import annotations

import logging

from django.db.models import Count
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import decorators, mixins, permissions, response, viewsets

from apps.course.models import Course
from apps.course.permissions import IsEnrolledInCourse
from apps.course.serializers import CourseSerializer
from apps.otl.sync import OtlSyncError, sync_user_courses

log = logging.getLogger(__name__)


class CourseViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = CourseSerializer
    permission_classes = (permissions.IsAuthenticated, IsEnrolledInCourse)
    pagination_class = None  # 한 학기 과목 수가 적어 페이지네이션 불필요

    def get_queryset(self):
        # 본인이 enroll 된 과목만. enrollment_count 는 `n명` 표시용 annotate.
        user = self.request.user
        qs = (
            Course.objects.filter(enrollments__user=user)
            .annotate(enrollment_count=Count("enrollments", distinct=True))
            .prefetch_related("professors")
        )

        year = self.request.query_params.get("year")
        semester = self.request.query_params.get("semester")
        if year is not None:
            qs = qs.filter(year=year)
        if semester is not None:
            qs = qs.filter(semester=semester)

        return qs.order_by("-year", "-semester", "course_code")

    @extend_schema(
        summary="본인 수강 과목 목록 조회 (필요시 OTL sync)",
        description=(
            "현재 로그인한 사용자의 수강 과목들을 반환한다. 마지막 OTL sync "
            "후 24시간이 지났으면 OTL 에 호출해서 enrollment 를 갱신한다 "
            "(드랍한 과목은 빠지고 새로 신청한 과목은 추가됨). `?refresh=true` "
            "로 강제 sync 가능."
        ),
        parameters=[
            OpenApiParameter(
                name="refresh",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description="true 로 주면 24h 캐시 무시하고 강제 OTL sync.",
                required=False,
            ),
            OpenApiParameter(
                name="year",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="개설 연도 필터 (예: 2026)",
                required=False,
            ),
            OpenApiParameter(
                name="semester",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="학기 (1=봄, 2=여름, 3=가을, 4=겨울)",
                required=False,
            ),
        ],
        responses=CourseSerializer(many=True),
    )
    @decorators.action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        force = request.query_params.get("refresh", "").lower() in ("1", "true", "yes")
        try:
            sync_user_courses(request.user, force=force)
        except OtlSyncError as e:
            # OTL 다운/장애여도 stale enrollment 로 계속 응답 (UX 우선).
            log.warning("OTL sync failed for user %s, falling back: %r", request.user.id, e)

        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return response.Response(serializer.data)

    @extend_schema(
        summary="과목 게시판 카탈로그 (학기 필터 가능)",
        description=(
            "본인이 수강 중/수강했던 과목 목록을 반환한다. 외부 catalog 가 "
            "아니라 enrollment 기반 본인 과목만 노출. `/me/` 와 달리 OTL sync 는 "
            "트리거하지 않는다."
        ),
        parameters=[
            OpenApiParameter(
                name="year",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="개설 연도 필터 (예: 2026)",
                required=False,
            ),
            OpenApiParameter(
                name="semester",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="학기 (1=봄, 2=여름, 3=가을, 4=겨울)",
                required=False,
            ),
        ],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="과목 게시판 단건 조회")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
