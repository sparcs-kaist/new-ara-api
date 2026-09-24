from django.urls import include, path

from apps.major.views.me import MeView
from apps.major.views.router import router

urlpatterns = [
    path("api/", include(router.urls)),
    path("api/majors/me/", view=MeView.as_view(), name="major-me"),
]
