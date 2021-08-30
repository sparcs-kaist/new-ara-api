import re

from channels.generic.websocket import AsyncJsonWebsocketConsumer

class WebSocketHandler(AsyncJsonWebsocketConsumer):

    # there is only one channel group
    groups = ['broadcast']

    article_id_regex = re.compile(r'^https://[a-z.]+/post/(\d+)/?(\?.*)?$')
    board_regex = re.compile(r'^https://[a-z.]+/(board|archive)(/[a-z-]+)?/?(\?.*)?$')

    async def connect(self):
        self.watching_article = -1
        await self.accept()

    async def disconnect(self, code):
        pass

    async def receive_json(self, content, **kwargs):
        match = WebSocketHandler.article_id_regex.match(content['new_route'])
        if match:
            self.watching_article = int(match.group(1))
        else:
            self.watching_article = 0 if WebSocketHandler.board_regex.match(content['new_route']) else -1

    async def update_articlelist(self, event):
        """
        Notify if the client is watching the articlelist.
        """
        if self.watching_article == 0:
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