"""특정 Major 안의 Article CRUD.

URL: /api/majors/<std_dept_id>/articles/[<pk>/]
권한: IsSameMajor (sso std_dept_id 가 URL std_dept_id 와 일치해야 read/write 가능)
글은 닉네임(REGULAR), parent_board 는 dummy "major-articles-internal" 로 강제.
Major row 는 접근 시 SSO 정보로 lazy get_or_create 된다.
"""

from __future__ import annotations

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, response, status, viewsets

from apps.core.models import Article
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
    # 실제 조회는 get_queryset() 이 담당한다. 여기 빈 queryset 을 두는 건
    # 스키마 생성기가 URL kwargs 없이 get_queryset() 을 호출하다 KeyError 를
    # 내는 것을 막기 위함.
    queryset = Article.objects.none()
    lookup_value_regex = "[0-9]+"
    # ModelViewSet 은 PUT(update) 도 갖고 있지만 학과글은 부분 수정만 지원한다.
    # 라우터에 맡기면 PUT 이 자동 노출되므로 여기서 막는다.
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
        # related_major 는 Major(PK=std_dept_id) FK 이므로 related_major_id 가
        # 곧 std_dept_id. URL 값으로 바로 필터한다.
        std_dept_id = self.kwargs["std_dept_id"]
        return (
            Article.objects.filter(related_major_id=std_dept_id)
            # 마스킹 판정(hidden_reasons)과 작성자 표기가 매 row 마다
            # parent_board / created_by.profile 을 보므로 같이 당겨온다.
            .select_related("created_by__profile", "parent_board").order_by(
                "-created_at"
            )
        )

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        # core 와 동일하게 ?override_hidden 으로 마스킹 해제를 요청할 수 있다.
        # (해제 가능한 사유인지는 serializer 가 CAN_OVERRIDE_REASONS 로 판단)
        ctx["override_hidden"] = "override_hidden" in self.request.query_params
        std_dept_id = self.kwargs.get("std_dept_id")
        if std_dept_id is not None:
            user = self.request.user
            if int(std_dept_id) == user_major_id(user):
                # 내 SSO 학과: 없으면 SSO 정보로 lazy 생성 (첫 접근).
                ctx["major"] = get_or_create_major_for_user(user)
            else:
                # add 한 타 학과: 이미 존재하는 row (읽기 전용). 생성하지 않는다.
                ctx["major"] = get_object_or_404(Major, pk=std_dept_id)
            ctx["board_id"] = get_major_board_id()
        return ctx

    @extend_schema(summary="학과 게시판 글 목록")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="학과 게시판 글 작성",
        description=(
            "현재 사용자가 해당 학과여야 작성 가능. "
            "name_type 은 닉네임(REGULAR), parent_board 는 dummy major-articles "
            "board 로 자동 set."
        ),
        request=MajorArticleCreateSerializer,
        responses={201: MajorArticleSerializer},
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        article = serializer.save()
        # 읽기 serializer 는 마스킹 판정에 context["request"] 를 쓰므로
        # context 없이 만들면 KeyError 가 난다.
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
