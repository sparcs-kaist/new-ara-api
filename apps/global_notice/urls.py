from django.urls import include, path

from apps.global_notice.views import GlobalNoticeViewSet

urlpatterns = [path("api/global_notice", GlobalNoticeViewSet.as_view())]
