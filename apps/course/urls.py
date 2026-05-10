from django.urls import include, path

from apps.course.views.router import router
from apps.course.views.viewsets.article import CourseArticleViewSet

urlpatterns = [
    path("api/", include(router.urls)),
    path(
        "api/courses/<int:course_id>/articles/",
        CourseArticleViewSet.as_view(
            {"get": "list", "post": "create"}
        ),
        name="course-article-list",
    ),
    path(
        "api/courses/<int:course_id>/articles/<int:pk>/",
        CourseArticleViewSet.as_view(
            {
                "get": "retrieve",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="course-article-detail",
    ),
]
