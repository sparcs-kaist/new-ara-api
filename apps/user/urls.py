from django.urls import include, path

from apps.user.views.fcmtoken import FCMTokenView
from apps.user.views.me import MeView
from apps.user.views.router import router
from apps.user.views.unregister import Unregister

urlpatterns = [
    path("", include(router.urls)),
    path("me", MeView.as_view(), name="me"),
    path("unregister", Unregister.as_view(), name="unregister"),
    path("fcm_token/<mode>", FCMTokenView.as_view(), name="fcm"),
]
