from rest_framework.routers import DefaultRouter

from apps.course.views.viewsets.course import CourseViewSet
from apps.course.views.viewsets.group import CourseGroupViewSet

router = DefaultRouter()
router.register(prefix=r"courses", viewset=CourseViewSet, basename="course")
router.register(
    prefix=r"course-groups", viewset=CourseGroupViewSet, basename="course-group"
)
