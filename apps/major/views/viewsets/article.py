"""특정 Major 안의 Article CRUD.

URL: /api/majors/<major_id>/articles/[<pk>/]
권한: Read : Anyone / Write : IsAuthenticated + ReadAuthWriteOwnMajor (major_id 로 major 게시판 소유권 확인)
모든 글은 익명, parent_board 는 dummy "major-articles-internal" 로 강제.
"""

from __future__ import annotations

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, response, status, viewsets

from apps.core.models import Article
from apps.major.board import get_major_board_id
from apps.major.models import Major
from apps.major.permissions import ReadAuthWriteOwnMajor
from apps.major.serializers import (
    MajorArticleCreateSerializer,
    MajorArticleListSerializer,
    MajorArticleSerializer,
    MajorArticleUpdateSerializer,
)


@extend_schema_view(
    list=extend_schema(tags=["major"]),
    create=extend_schema(tags=["major"]),
    retrieve=extend_schema(tags=["major"]),
    partial_update=extend_schema(tags=["major"]),
    destroy=extend_schema(tags=["major"]),
)
class MajorArticleViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated, ReadAuthWriteOwnMajor)
    serializer_class = MajorArticleSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MajorArticleListSerializer
        if self.action == "create":
            return MajorArticleCreateSerializer
        if self.action in ("update", "partial_update"):
            return MajorArticleUpdateSerializer
        return MajorArticleSerializer

    def get_queryset(self):
        major_id = self.kwargs["major_id"]
        return (
            Article.objects.filter(related_major_id=major_id)
            .order_by("-created_at")
        )

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        major_id = self.kwargs.get("major_id")
        if major_id is not None:
            ctx["major"] = get_object_or_404(Major, pk=major_id)
            ctx["board_id"] = get_major_board_id()
        return ctx

    @extend_schema(summary="학과 게시판 글 목록")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="학과 게시판 글 작성 (익명 강제)",
        description=(
            "현재 사용자가 해당 학과여야 작성 가능 "
            "name_type 은 항상 ANONYMOUS, parent_board 는 dummy major-articles "
            "board 로 자동 set."
        ),
        request=MajorArticleCreateSerializer,
        responses={201: MajorArticleSerializer},
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        article = serializer.save()
        out = MajorArticleSerializer(article).data
        return response.Response(out, status=status.HTTP_201_CREATED)

    @extend_schema(summary="학과 게시판 글 상세")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(summary="학과 게시판 글 수정")
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(summary="학과 게시판 글 삭제 (soft delete)")
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
