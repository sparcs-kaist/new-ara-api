from rest_framework import routers

from apps.user.views.viewsets import *


router = routers.SimpleRouter()


# UserProfileViewSet

router.register(
    prefix=r'user_profiles',
    viewset=UserProfileViewSet,
)
