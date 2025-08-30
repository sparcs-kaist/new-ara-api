from django.urls import path, include
from .views.router import router

urlpatterns = [
    path("api/", include(router.urls)),
]