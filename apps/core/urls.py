from django.urls import include, path

from apps.core.views import HomeView, InvalidSsoLoginView, StatusView, router

urlpatterns = [
    path("", include(router.urls)),
    path("home/", view=HomeView.as_view(), name="HomeView"),
    path("status/", view=StatusView.as_view(), name="StatusView"),
    path(
        "invalid_sso_login/",
        InvalidSsoLoginView.as_view(),
        name="InvalidSsoLoginView",
    ),
]
