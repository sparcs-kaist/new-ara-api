"""학과 게시판 전체 목록 + 유저의 타 학과 추가/제거.

- GET  /api/majors/                              : 존재하는 학과 게시판 전체 목록
- GET  /api/majors/my-major/                     : 내가 추가한(add) 학과 게시판 목록
- POST /api/majors/<std_dept_id>/user_major_add/    : 타 학과 게시판을 내 목록에 추가(읽기용)
- POST /api/majors/<std_dept_id>/user_major_remove/ : 추가한 학과 게시판을 내 목록에서 제거

추가한 학과는 '읽기 전용'으로 볼 수 있다 (쓰기는 여전히 SSO 학과만). 자기 SSO
학과는 add 없이도 항상 접근되므로 add/remove 대상이 아니다.
"""

from __future__ import annotations

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, permissions, response, status, viewsets

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
    queryset = Major.objects.all().order_by("std_dept_id")

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        # is_added 계산용. 목록 전체를 한 번의 쿼리로 (N+1 방지).
        ctx["added_major_ids"] = user_added_major_ids(self.request.user)
        return ctx

    @extend_schema(tags=["major"], summary="내가 볼 수 있는 학과 게시판 목록 (내 학과 + 추가한 학과)")
    def my_major(self, request):
        user = request.user
        # 내가 add 한 타 학과들 (UserMajor / readers M2M 경유).
        majors = list(
            Major.objects.filter(readers=user).order_by("std_dept_id")
        )
        # 내 SSO 학과도 포함 (add 없이도 항상 접근 가능). 없으면 lazy 생성 후 맨 앞에.
        home = get_or_create_major_for_user(user)
        if home is not None and home not in majors:
            majors.insert(0, home)
        serializer = self.get_serializer(majors, many=True)
        return response.Response(serializer.data)

    @extend_schema(tags=["major"], summary="타 학과 게시판 추가 (읽기용)")
    def user_major_add(self, request, std_dept_id=None):
        major = get_object_or_404(Major, pk=std_dept_id)

        # 내 SSO 학과는 add 없이도 접근 가능 → 추가 대상 아님.
        if major.std_dept_id == user_major_id(request.user):
            return response.Response(
                {"detail": "본인 학과는 추가할 필요가 없습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        UserMajor.objects.get_or_create(user=request.user, major=major)
        return response.Response(status=status.HTTP_201_CREATED)

    @extend_schema(tags=["major"], summary="추가한 학과 게시판 제거")
    def user_major_remove(self, request, std_dept_id=None):
        UserMajor.objects.filter(
            user=request.user, major_id=std_dept_id
        ).delete()
        return response.Response(status=status.HTTP_204_NO_CONTENT)
