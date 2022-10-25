from rest_framework import routers

from apps.user.views.viewsets import UserViewSet, UserProfileViewSet

router = routers.DefaultRouter()

# UserViewSet
router.register(
    prefix=r"users",
    viewset=UserViewSet,
)

# UserProfileViewSet
router.register(
    prefix=r"user_profiles",
    viewset=UserProfileViewSet,
)
