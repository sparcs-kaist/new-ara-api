"""특정 Course 안의 Article CRUD.

URL: /api/courses/<course_id>/articles/[<pk>/]
권한: IsEnrolledInCourse (course_id 로 enrollment 확인)
모든 글은 익명, parent_board 는 dummy "course-articles-internal" 로 강제.
"""

from __future__ import annotations

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, response, status, viewsets

from apps.core.models import Article
from apps.course.board import get_courses_board_id
from apps.course.models import Course
from apps.course.permissions import IsEnrolledInCourse
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
    permission_classes = (permissions.IsAuthenticated, IsEnrolledInCourse)
    serializer_class = CourseArticleSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return CourseArticleListSerializer
        if self.action == "create":
            return CourseArticleCreateSerializer
        if self.action in ("update", "partial_update"):
            return CourseArticleUpdateSerializer
        return CourseArticleSerializer

    def get_queryset(self):
        course_id = self.kwargs["course_id"]
        return (
            Article.objects.filter(related_course_id=course_id)
            .order_by("-created_at")
        )

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        course_id = self.kwargs.get("course_id")
        if course_id is not None:
            ctx["course"] = get_object_or_404(Course, pk=course_id)
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
