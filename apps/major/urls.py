from django.urls import path

from apps.major.views.viewsets.article import MajorArticleViewSet
from apps.major.views.viewsets.major import MajorViewSet
from apps.major.views.me import MeView

urlpatterns = [
    path("api/majors/", MajorViewSet.as_view({"get": "list"}), name="major-list"),
    path("api/majors/my-major/", MajorViewSet.as_view({"get": "my_major"}), name="major-my-major"),
    path("api/majors/me/", MeView.as_view(), name="major-me"),
    path("api/majors/<int:std_dept_id>/user_major_add/", MajorViewSet.as_view({"post": "user_major_add"}), name="major-user-add"),
    path("api/majors/<int:std_dept_id>/user_major_remove/", MajorViewSet.as_view({"post": "user_major_remove"}), name="major-user-remove"),
    path("api/majors/<int:std_dept_id>/articles/", MajorArticleViewSet.as_view({"get": "list", "post": "create"}), name="major-article-list"),
    path("api/majors/<int:std_dept_id>/articles/<int:pk>/", MajorArticleViewSet.as_view({"get": "retrieve", "patch": "partial_update", "delete": "destroy"}), name="major-article-detail"),
]

