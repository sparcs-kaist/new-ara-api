from django.conf.urls import url, include

from apps.core.views import *
from apps.core.views.router import *


urlpatterns = [
    url(r'^api/', include(router.urls)),

    url(
        regex=r'^api/home/$',
        view=HomeView.as_view(),
        name='HomeView',
    ),
]
