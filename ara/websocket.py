import json

from asgiref.sync import async_to_sync
from channels.auth import AuthMiddlewareStack
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from channels.routing import ProtocolTypeRouter, URLRouter
from django.conf import settings
from django.urls import path
from django.core.asgi import get_asgi_application


channel_layer = get_channel_layer()


class WebSocketHandler(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add('default', self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard('default', self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        # Echo
        await self.channel_layer.group_send('default', {
            'type': 'send_message',
            'message': text_data
        })

    async def send_message(self, event):
        await self.send(event['message'])


def send_message(instance, state, objects, silent=True, sync=True):
    """
    알림을 보낸다.
    :param instance: 어떤 데이터에 변화가 일어났는지 (예: article, comment, ...)
    :param state: created, updated, deleted
    :param objects: 변화가 일어난 데이터들의 리스트 (예: [{"id": 1, "positive_vote_count" 10, ...}, ...]
    :param silent: silent noti 여부
    :param sync: False면 async
    """
    if settings.TEST:
        return

    message_dict = {
        'silent': silent,
        'instance': instance,
        'state': state,
        'objects': objects,
    }

    group_send = async_to_sync(channel_layer.group_send) if sync else channel_layer.group_send
    return group_send('default', {
        'type': 'send_message',
        'message': json.dumps(message_dict)
    })


application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter([path('ws/', WebSocketHandler.as_asgi())])
    ),
})