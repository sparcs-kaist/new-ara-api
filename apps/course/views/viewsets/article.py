"""특정 Course 가 속한 그룹의 Article CRUD.

URL: /api/courses/<course_id>/articles/[<pk>/]
게시판 단위는 course 가 아니라 그 course 의 CourseGroup — 학기가 달라도
같은 수업이면 글이 누적된다. course_id 는 "어느 학기에서 들어왔나"의 진입점.
권한: IsEnrolledInCourseGroup (그룹의 아무 학기라도 수강했으면 접근).
모든 글은 익명, parent_board 는 dummy "course-articles-internal" 로 강제.
"""

from __future__ import annotations

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, response, status, viewsets

from apps.core.models import Article
from apps.course.board import get_courses_board_id
from apps.course.models import Course
from apps.course.permissions import IsEnrolledInCourseGroup
from apps.course.serializers import (
    CourseArticleCreateSerializer,
    CourseArticleListSerializer,
    CourseArticleSerializer,
    CourseArticleUpdateSerializer,
)


@extend_schema_view(
    list=extend_schema(tags=["course"]),
    create=extend_schema(tags=["course"]),
    retrieve=extend_schema(tags=["course"]),
    partial_update=extend_schema(tags=["course"]),
    destroy=extend_schema(tags=["course"]),
)
class CourseArticleViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated, IsEnrolledInCourseGroup)
    serializer_class = CourseArticleSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return CourseArticleListSerializer
        if self.action == "create":
            return CourseArticleCreateSerializer
        if self.action in ("update", "partial_update"):
            return CourseArticleUpdateSerializer
        return CourseArticleSerializer

    def _get_course(self):
        return get_object_or_404(Course, pk=self.kwargs["course_id"])

    def get_queryset(self):
        # 글 묶음은 course 가 아니라 그 course 의 group. 모든 학기 글이 누적된다.
        course = self._get_course()
        return (
            Article.objects.filter(related_course_group_id=course.group_id)
            .order_by("-created_at")
        )

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        if self.kwargs.get("course_id") is not None:
            course = self._get_course()
            ctx["course"] = course  # 출처 (related_course)
            ctx["course_group"] = course.group  # 게시판 묶음 (related_course_group)
            ctx["board_id"] = get_courses_board_id()
        return ctx

    @extend_schema(summary="과목 게시판 글 목록")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="과목 게시판 글 작성 (익명 강제)",
        description=(
            "현재 사용자가 해당 과목에 enroll 되어 있어야 작성 가능. "
            "name_type 은 항상 ANONYMOUS, parent_board 는 dummy course-articles "
            "board 로 자동 set."
        ),
        request=CourseArticleCreateSerializer,
        responses={201: CourseArticleSerializer},
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        article = serializer.save()
        out = CourseArticleSerializer(article).data
        return response.Response(out, status=status.HTTP_201_CREATED)

    @extend_schema(summary="과목 게시판 글 상세")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(summary="과목 게시판 글 수정")
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(summary="과목 게시판 글 삭제 (soft delete)")
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def perform_update(self, serializer):
        # 작성자만 수정 허용
        article = self.get_object()
        if article.created_by_id != self.request.user.id:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("본인이 작성한 글만 수정할 수 있습니다.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.created_by_id != self.request.user.id:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("본인이 작성한 글만 삭제할 수 있습니다.")
        super().perform_destroy(instance)
