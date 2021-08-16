import re

from channels.generic.websocket import AsyncJsonWebsocketConsumer

class WebSocketHandler(AsyncJsonWebsocketConsumer):

    # there is only one channel group
    groups = ['broadcast']

    article_id_regex = re.compile(r'/post/(\d+)$')

    async def connect(self):
        self.watching_article = 0
        await self.accept()

    async def disconnect(self, code):
        pass

    async def receive_json(self, content, **kwargs):
        match = WebSocketHandler.article_id_regex.search(content['new_route'])
        self.watching_article = int(match.group(1)) if match else 0

    # websocket sessions are not preserved between pages
    async def update_articlelist(self, event):
        """
        Notify if the client is watching the articlelist.
        """
        if not self.watching_article:
            await self.send_json({
                'msg_type': 'update',
                'target': 'articlelist',
            })

    async def update_articleview(self, event):
        """
        Notify if the client is watching a specific article.
        """
        if self.watching_article == int(event['post_id']):
            await self.send_json({
                'msg_type': 'update',
                'target': 'articleview',
            })

    async def update_notification(self, event):
        """
        Notify if the client's user has a new notification.
        """
        if self.scope['user'].id == event['user_id']:
            await self.send_json({
                'msg_type': 'update',
                'target': 'notification',
            })