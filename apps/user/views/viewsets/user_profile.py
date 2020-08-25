from rest_framework import mixins, response

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
