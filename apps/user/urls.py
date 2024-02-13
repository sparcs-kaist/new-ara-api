from django.urls import include, path

from apps.user.views.fcm import FCMTokenView, FCMTopicView
from apps.user.views.me import MeView
from apps.user.views.router import router

urlpatterns = [
    path("api/", include(router.urls)),
    path("api/me", MeView.as_view(), name="me"),
    path("api/fcm/token/<mode>/", FCMTokenView.as_view(), name="fcm_token"),
    path("api/fcm/topic/", FCMTopicView.as_view(), name="fcm_topic"),
]
