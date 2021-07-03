from channels.generic.websocket import AsyncJsonWebsocketConsumer

from channels.auth import get_user


class WebSocketHandler(AsyncJsonWebsocketConsumer):

    # there is only one channel group
    groups = ['broadcast']

    async def connect(self):
        # TODO: websocket scope does not give appropriate user(scope['user'] is always anonymous). Need to fix
        await self.accept()

    async def disconnect(self, code):
        pass

    async def receive_json(self, content, **kwargs):
        """
        Receive handler. Do nothing since there is no usage now. 
        """
        pass


    # websocket sessions are not preserved between pages
    async def update_articlelist(self, event):
        """
        Notify if the client is watching the articlelist.
        """
        if 'post_id' not in self.scope['url_route']['kwargs']:
            await self.send_json({
                'msg_type': 'update',
                'target': 'articlelist',
            })

    async def update_articleview(self, event):
        """
        Notify if the client is watching a specific article.
        """
        if self.scope['url_route']['kwargs'].get('post_id') == str(event['post_id']):
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