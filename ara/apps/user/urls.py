from django.urls import path, include

from apps.user.views.router import *

urlpatterns = [
    path('api/', include(router.urls)),
]
