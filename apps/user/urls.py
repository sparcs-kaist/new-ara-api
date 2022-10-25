from django.urls import path, include

from apps.user.views.router import router
from apps.user.views.me import MeView

urlpatterns = [
    path("api/", include(router.urls)),
    path("api/me", MeView.as_view(), name="me"),
]
