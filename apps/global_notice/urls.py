from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import GlobalNoticeViewSet

router = DefaultRouter()
router.register("", GlobalNoticeViewSet, basename="global_notices")


urlpatterns = [
    path("api/global_notices/", include(router.urls)),
]
