from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import GlobalNoticeViewSet

router = DefaultRouter()
router.register(r"api/global_notices", GlobalNoticeViewSet, basename="global_notices")

urlpatterns = router.urls
