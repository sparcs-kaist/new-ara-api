from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.global_notice.views import GlobalNoticeViewSet

router = DefaultRouter()
router.register(r"/api/globalNotice", GlobalNoticeViewSet, basename="globalNotice")

urlpatterns = router.urls
