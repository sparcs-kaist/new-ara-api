from django.urls import path, include
from .views.router import router

urlpatterns = [
    path("", include(router.urls)),
]