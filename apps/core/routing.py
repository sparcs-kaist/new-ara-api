from django.urls import re_path

from .consumers import WebSocketHandler

websocket_urlpatterns = [
    re_path(r'ws/default_endpoint/$', WebSocketHandler.as_asgi()),
]