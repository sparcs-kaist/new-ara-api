from django.utils import timezone

from rest_framework import decorators, mixins, response, status

from ara.classes.viewset import ActionAPIViewSet

from apps.user.models import UserProfile
from apps.user.permissions.user_profile import UserProfilePermission
from apps.user.serializers.user_profile import (
    UserProfileSerializer,
    UserProfileUpdateActionSerializer,
    PublicUserProfileSerializer,
)


class UserProfileViewSet(mixins.RetrieveModelMixin,
                         mixins.UpdateModelMixin,
                         ActionAPIViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    action_serializer_class = {
        'update': UserProfileUpdateActionSerializer,
        'partial_update': UserProfileUpdateActionSerializer,
    }
    permission_classes = (
        UserProfilePermission,
    )

    def retrieve(self, request, *args, **kwargs):
        profile = self.get_object()
        if request.user == profile.user:
            return super().retrieve(request, *args, **kwargs)
        else:
            return response.Response(PublicUserProfileSerializer(profile).data)

    @decorators.action(detail=True, methods=['patch'])
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
