from django.conf.urls import url, include

from apps.session.views import *
from apps.session.views.router import *


urlpatterns = [
    url(r'^api/', include(router.urls)),

    url(r'^login/$', user_login),
    url(r'^login/callback/$', login_callback),
    url(r'^logout/$', user_logout),
    url(r'^unregister/$', unregister),
    url(r'^test/$', login_test),
]
