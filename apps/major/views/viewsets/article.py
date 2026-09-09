"""특정 Major 안의 Article CRUD.

URL: /api/majors/<std_dept_id>/articles/[<pk>/]
권한: 읽기는 SSO 학과 또는 즐겨찾기 학과, 쓰기는 SSO 학과만 가능하다.
글 작성 시 익명 또는 닉네임을 선택하고, parent_board 는 dummy
"major-articles-internal" 로 강제한다.
Major row 는 접근 시 SSO 정보로 lazy get_or_create 된다.
"""

from __future__ import annotations

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, response, status, viewsets

from apps.core.models import Article, Comment, Vote
from apps.major.access import get_or_create_major_for_user, user_major_id
from apps.major.board import get_major_board_id
from apps.major.models import Major
from apps.major.permissions import IsSameMajor
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
    permission_classes = (permissions.IsAuthenticated, IsSameMajor)
    serializer_class = MajorArticleSerializer
    # Empty QuerySet은 schema generator가 URL kwargs 없이 조회할 때의 `KeyError`를 막는다.
    queryset = Article.objects.none()
    lookup_value_regex = "[0-9]+"
    # `ModelViewSet`의 default PUT을 막고 partial update만 허용한다.
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_serializer_class(self):
        if self.action == "list":
            return MajorArticleListSerializer
        if self.action == "create":
            return MajorArticleCreateSerializer
        if self.action in ("update", "partial_update"):
            return MajorArticleUpdateSerializer
        return MajorArticleSerializer

    def get_queryset(self):
        # `related_major_id`는 `Major` PK이므로 URL의 `std_dept_id`로 바로 filter한다.
        std_dept_id = self.kwargs["std_dept_id"]
        queryset = (
            Article.objects.filter(related_major_id=std_dept_id)
            # Masking과 author rendering의 per-row query를 막기 위해 related objects를 join한다.
            .select_related("created_by__profile", "parent_board").order_by(
                "-created_at"
            )
        )
        if self.action == "retrieve":
            queryset = queryset.prefetch_related(
                Vote.prefetch_my_vote(self.request.user),
                Comment.prefetch_for_article(self.request.user),
            )
        return queryset

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        # Core와 같이 `override_hidden`을 지원하며 serializer가 override 가능 여부를 판단한다.
        ctx["override_hidden"] = "override_hidden" in self.request.query_params
        std_dept_id = self.kwargs.get("std_dept_id")
        if std_dept_id is not None:
            user = self.request.user
            if int(std_dept_id) == user_major_id(user):
                # SSO home major가 없으면 first access에서 lazy-create한다.
                ctx["major"] = get_or_create_major_for_user(user)
            else:
                # Favorite major는 read/vote만 허용하며 existing row를 사용한다.
                ctx["major"] = get_object_or_404(Major, pk=std_dept_id)
            ctx["board_id"] = get_major_board_id()
        return ctx

    @extend_schema(summary="학과 게시판 글 목록")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="학과 게시판 글 작성 (익명/닉네임 선택)",
        description=(
            "현재 사용자가 해당 학과여야 작성 가능. "
            "name_type 은 ANONYMOUS 또는 REGULAR이며, 생략하면 기존 동작과 "
            "같이 REGULAR로 저장. parent_board 는 dummy major-articles "
            "board로 자동 set."
        ),
        request=MajorArticleCreateSerializer,
        responses={201: MajorArticleSerializer},
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        article = serializer.save()
        # Read serializer의 masking logic에 필요한 request context를 전달한다.
        out = MajorArticleSerializer(
            article, context=self.get_serializer_context()
        ).data
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
        # Author만 update할 수 있다.
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
