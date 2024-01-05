from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import EventViewSet, TagViewSet

router = DefaultRouter()
router.register(r"events", EventViewSet, basename="event")
router.register(r"tags", TagViewSet, basename="tag")

urlpatterns = [
    path("api/calendar/", include(router.urls)),
]
