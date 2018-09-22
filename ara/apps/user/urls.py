from django.conf.urls import url, include

from apps.user.views.router import *


urlpatterns = [
    url(r'^api/', include(router.urls)),
]
