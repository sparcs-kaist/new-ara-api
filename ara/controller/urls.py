from django.urls import path

from ara.controller.api import api

urlpatterns = [
    path(
        "",
        api.urls,
    )
]
