from django.urls import re_path

from .consumers import WebSocketHandler

websocket_urlpatterns = [
    re_path(r'ws/articles/$', WebSocketHandler.as_asgi()),
    re_path(r'ws/articles/(?P<post_id>[0-9]+)/$', WebSocketHandler.as_asgi()),
]