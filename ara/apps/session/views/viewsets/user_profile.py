from rest_framework import viewsets

from ara.classes.viewset import ActionAPIViewSet

from apps.session.models import UserProfile
from apps.session.serializers.user_profile import UserProfileSerializer


class UserProfileViewSet(viewsets.ModelViewSet, ActionAPIViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
