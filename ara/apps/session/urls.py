from django.conf.urls import url, include

from apps.session import views
from apps.session.views.router import *


urlpatterns = [
    url(r'^api/', include(router.urls)),

    url(r'^login/$', views.user_login),
    url(r'^login/callback/$', views.login_callback),
    url(r'^logout/$', views.user_logout),
    url(r'^unregister/$', views.unregister),
    url(r'^test/$', views.login_test),
]

