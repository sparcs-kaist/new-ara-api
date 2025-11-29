from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.portal_notice import PortalNoticeView

router = DefaultRouter()
router.register(r'portal_notice', PortalNoticeView, basename='portal_notice')

urlpatterns = [
    path("", include(router.urls)),
]