from django.urls import include, path

from apps.core.views import HomeView, InvalidSsoLoginView, StatusView, router

urlpatterns = [
    path("api/", include(router.urls)),
    path("api/home/", view=HomeView.as_view(), name="HomeView"),
    path("api/status/", view=StatusView.as_view(), name="StatusView"),
    path(
        "api/invalid_sso_login/",
        InvalidSsoLoginView.as_view(),
        name="InvalidSsoLoginView",
    ),
]
