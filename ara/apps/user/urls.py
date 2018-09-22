from django.conf.urls import url, include

from apps.user.views import *
from apps.user.views.router import *


urlpatterns = [
    url(r'^api/', include(router.urls)),

    url(r'^login/$', user_login),
    url(r'^login/callback/$', login_callback),
    url(r'^unregister/$', unregister),
    url(r'^old-ara-login/$', old_ara_login)
]
