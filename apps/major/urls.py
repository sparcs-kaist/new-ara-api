from django.urls import path

from apps.major.views.viewsets.article import MajorArticleViewSet
from apps.major.views.me import MeView

urlpatterns = [
    path("api/majors/<int:major_id>/articles/", MajorArticleViewSet.as_view({"get": "list", "post": "create"}), name="major-article-list"),
    path("api/majors/<int:major_id>/articles/<int:pk>/", MajorArticleViewSet.as_view({"get": "retrieve", "patch": "partial_update", "delete": "destroy"}), name="major-article-detail"),
    path("api/majors/me/", MeView.as_view(), name="major-me"),]

