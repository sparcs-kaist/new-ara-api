from rest_framework import routers

from apps.session.views.viewsets import *


router = routers.SimpleRouter()


# UserProfileViewSet

router.register(
    prefix=r'user_profiles',
    viewset=UserProfileViewSet,
)
