from django.urls import include, path

from apps.course.views.router import router
from apps.major.views.viewsets.article import MajorArticleViewSet
from apps.user.views.me import MeView

url_patterns = [path("api/", include(router.urls)),
                path("api/majors/<int:major_id>/articles/", MajorArticleViewSet.as_view({"get": "list", "post": "create"}), name="major-article-list"),
                path("api/majors/<int:major_id>/articles/<int:pk>/", MajorArticleViewSet.as_view({"get": "retrieve", "patch": "partial_update", "delete": "destroy"}), name="major-article-detail"),
                path("api/majors/me/", MeView.as_view(name="major-me")),]

