from rest_framework.routers import DefaultRouter

from apps.course.views.viewsets.course import CourseViewSet

router = DefaultRouter()
router.register(prefix=r"courses", viewset=CourseViewSet, basename="course")
