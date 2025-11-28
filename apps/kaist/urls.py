from django.urls import path
from .views.portal_notice import PortalNoticeView

urlpatterns = [
    path("portal_notice/", PortalNoticeView.as_view(), name="portal_notice"),
]