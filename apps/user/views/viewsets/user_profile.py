from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework import decorators, mixins, response, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.pagination import PageNumberPagination

from apps.user.models import UserProfile
from apps.user.permissions.user_profile import UserProfilePermission
from apps.user.serializers.user_profile import (
    PublicUserProfileSerializer,
    PublicUserProfileSearchSerializer,  # Import the search serializer
    UserProfileSerializer,
    UserProfileUpdateActionSerializer,
)
from ara.classes.viewset import ActionAPIViewSet


class UserProfileViewSet(
    mixins.RetrieveModelMixin, mixins.UpdateModelMixin, ActionAPIViewSet, viewsets.GenericViewSet
):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    action_serializer_class = {
        "update": UserProfileUpdateActionSerializer,
        "partial_update": UserProfileUpdateActionSerializer,
    }
    permission_classes = (UserProfilePermission,)

    class Pagination(PageNumberPagination):
        page_size = 10
        page_size_query_param = "page_size"

    def retrieve(self, request, *args, **kwargs):
        profile = self.get_object()
        if request.user == profile.user:
            return super().retrieve(request, *args, **kwargs)
        else:
            return response.Response(PublicUserProfileSerializer(profile).data)

    @decorators.action(detail=True, methods=["patch"])
    def agree_terms_of_service(self, request, *args, **kwargs):
        # BAD_REQUEST if user already agree with the terms of service
        if request.user.profile.agree_terms_of_service_at is not None:
            return response.Response(
                status=status.HTTP_400_BAD_REQUEST,
            )

        request.user.profile.agree_terms_of_service_at = timezone.now()
        request.user.profile.save()

        return response.Response(
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="query",
                description="닉네임 검색어",
                required=False,
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
            ),
        ],
        responses={200: PublicUserProfileSearchSerializer(many=True)},
    )
    @action(detail=False, methods=["get"], permission_classes=[AllowAny])
    def search(self, request):
        query = request.query_params.get("query", None)
        if query:
            # 검색어를 포함하는 모든 사용자 찾기
            queryset = UserProfile.objects.filter(nickname__icontains=query)

            # 페이지네이션 적용
            paginator = self.Pagination()
            result_page = paginator.paginate_queryset(queryset, request)
            if result_page is not None:
                serializer = PublicUserProfileSearchSerializer(result_page, many=True)
                return paginator.get_paginated_response(serializer.data)

            # 페이지네이션이 적용되지 않은 경우 (전체 결과 반환)
            serializer = PublicUserProfileSearchSerializer(queryset, many=True)
            return response.Response(serializer.data)
        else:
            return response.Response([])  # 검색어가 없는 경우 빈 리스트 반환
