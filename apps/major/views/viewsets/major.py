"""학과 게시판 전체 목록 + 유저의 타 학과 추가/제거.

- GET  /api/majors/                              : 존재하는 학과 게시판 전체 목록
- GET  /api/majors/my-major/                     : 내가 추가한(add) 학과 게시판 목록
- POST /api/majors/<std_dept_id>/user_major_add/    : 타 학과 게시판을 내 목록에 추가(읽기·투표용)
- POST /api/majors/<std_dept_id>/user_major_remove/ : 추가한 학과 게시판을 내 목록에서 제거

추가한 학과는 읽기와 글·댓글 투표가 가능하고, 글·댓글 작성/수정/삭제와
스크랩·신고는 SSO 학과에서만 가능하다. 자기 SSO 학과는 add/remove 대상이
아니지만 내부 readers_count와 my-major 조회를 위해 UserMajor row를 자동 생성한다.
"""

from __future__ import annotations

from django.db.models import Count
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import (
    decorators,
    mixins,
    permissions,
    response,
    status,
    viewsets,
)

from apps.major.access import (
    get_or_create_major_for_user,
    user_added_major_ids,
    user_major_id,
)
from apps.major.models import Major, UserMajor
from apps.major.serializers import MajorSerializer


@extend_schema_view(
    list=extend_schema(tags=["major"], summary="학과 게시판 전체 목록"),
)
class MajorViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = MajorSerializer
    pagination_class = None
    # Major 의 PK 가 곧 std_dept_id 라 URL 키워드도 같은 이름을 쓴다.
    # 라우터가 이 값으로 detail route 를 만든다: /api/majors/<std_dept_id>/...
    lookup_url_kwarg = "std_dept_id"
    lookup_value_regex = "[0-9]+"

    def get_queryset(self):
        # readers_count = UserMajor row 수. 자동 등록된 홈 학과 사용자와 직접
        # 즐겨찾기한 타 학과 사용자를 모두 포함한다.
        # M2M(readers) 대신 through 역참조로 세어 조인 하나로 끝낸다.
        return Major.objects.annotate(readers_count=Count("user_additions")).order_by(
            "std_dept_id"
        )

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        # is_added 계산용. UserMajor에는 홈 학과 자동 row도 들어가므로 홈에서도
        # true다. 목록 전체를 한 번의 쿼리로 가져와 N+1을 막는다.
        ctx["added_major_ids"] = user_added_major_ids(self.request.user)
        # is_mine 계산용 (홈 학과 vs 추가한 학과 구분).
        ctx["my_std_dept_id"] = user_major_id(self.request.user)
        return ctx

    @extend_schema(
        tags=["major"],
        summary="내가 볼 수 있는 학과 게시판 목록 (내 학과 + 추가한 학과)",
    )
    @decorators.action(detail=False, methods=["get"], url_path="my-major")
    def my_major(self, request):
        user = request.user
        # 홈 학과의 Major + 내부 구독용 UserMajor row를 보장한다. 사용자 관점의
        # 즐겨찾기 추가가 아니라 readers_count/my-major를 위한 자동 등록이다.
        home = get_or_create_major_for_user(user)
        home_id = home.std_dept_id if home is not None else None

        # 내가 읽는 모든 학과(홈 포함)를 pk__in 으로 거른다. filter(readers=user)
        # 를 annotate 와 같이 쓰면 조인이 겹쳐 readers_count 가 틀어지므로 회피.
        ids = user_added_major_ids(user)
        majors = list(self.get_queryset().filter(pk__in=ids))
        # 내 학과를 맨 앞으로.
        majors.sort(key=lambda m: (m.std_dept_id != home_id, m.std_dept_id))

        serializer = self.get_serializer(majors, many=True)
        return response.Response(serializer.data)

    @extend_schema(tags=["major"], summary="타 학과 게시판 추가 (읽기·투표용)")
    @decorators.action(
        detail=True,
        methods=["post"],
        url_path="user_major_add",
        url_name="user-add",
    )
    def user_major_add(self, request, std_dept_id=None):
        major = get_object_or_404(Major, pk=std_dept_id)

        # 내 SSO 학과의 UserMajor row는 내부적으로 자동 생성되므로 사용자가
        # 즐겨찾기로 다시 추가할 대상은 아니다.
        if major.std_dept_id == user_major_id(request.user):
            return response.Response(
                {"detail": "본인 학과는 추가할 필요가 없습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        UserMajor.objects.get_or_create(user=request.user, major=major)
        return response.Response(status=status.HTTP_201_CREATED)

    @extend_schema(tags=["major"], summary="추가한 학과 게시판 제거")
    @decorators.action(
        detail=True,
        methods=["post"],
        url_path="user_major_remove",
        url_name="user-remove",
    )
    def user_major_remove(self, request, std_dept_id=None):
        # 내 SSO 학과는 항상 독자로 집계돼야 하므로 제거 불가 (제거해도 다음 접근
        # 시 재생성되어 readers_count 만 어긋난다).
        if std_dept_id is not None and int(std_dept_id) == user_major_id(request.user):
            return response.Response(
                {"detail": "본인 학과는 제거할 수 없습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        UserMajor.objects.filter(user=request.user, major_id=std_dept_id).delete()
        return response.Response(status=status.HTTP_204_NO_CONTENT)
