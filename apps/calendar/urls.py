from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views.viewsets.calendar import CalendarViewSet, TagViewSet

router = DefaultRouter()
router.register(r"calendars", CalendarViewSet, basename="calendar")
router.register(r"tags", TagViewSet, basename="tag")

urlpatterns = [
    path("api/", include(router.urls)),
]
