from django.conf.urls import url
from django.urls import path, include

from apps.core.views import *
from apps.core.views.router import *

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/home/', view=HomeView.as_view(), name='HomeView'),
]
