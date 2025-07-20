from channels.generic.websocket import AsyncWebsocketConsumer
import json

#채팅 관련 Socket 을 핸들링하는 Consumer 클래스
class ChatRoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.room_name = None

    async def disconnect(self, close_code):
        if self.room_name:
            await self.channel_layer.group_discard(self.room_name, self.channel_name)
            # 필요하면 user_leave 등 이벤트를 방에 알림

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        event_type = data.get('type')

        if event_type == 'connect_room':
            await self.connect_room(data['room_id'])
        elif event_type == 'disconnect_room':
            await self.disconnect_room(data['room_id'])
        elif event_type == 'typing_start':
            await self.typing_start()
        elif event_type == 'message_new':
            await self.message_new(data['message'])
        # 여기에 더 필요한 이벤트 타입 추가

    async def connect_room(self, room_id):
        # 기존에 접속한 방 있으면 나가기
        if self.room_name:
            await self.channel_layer.group_discard(self.room_name, self.channel_name)
        self.room_name = f'chat_{room_id}'
        await self.channel_layer.group_add(self.room_name, self.channel_name)

        # 방에 접속한 걸 알림 (user_join)
        await self.channel_layer.group_send(
            self.room_name,
            {
                'type': 'user_join',
                'user': self.channel_name,  # 실제론 유저 id 등
            }
        )

    async def disconnect_room(self, room_id):
        room_name = f'chat_{room_id}'
        await self.channel_layer.group_discard(room_name, self.channel_name)

        await self.channel_layer.group_send(
            room_name,
            {
                'type': 'user_leave',
                'user': self.channel_name,
            }
        )

    async def typing_start(self):
        # typing_start 이벤트를 그룹에 브로드캐스트
        if not self.room_name:
            return
        await self.channel_layer.group_send(
            self.room_name,
            {
                'type': 'user_typing',
                'user': self.channel_name,
            }
        )

    async def message_new(self, message):
        if not self.room_name:
            return
        await self.channel_layer.group_send(
            self.room_name,
            {
                'type': 'message_new',
                'message': message,
                'user': self.channel_name,
            }
        )

    # 그룹에서 이벤트 받는 핸들러들

    async def user_join(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_join',
            'user': event['user'],
        }))

    async def user_leave(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_leave',
            'user': event['user'],
        }))

    async def user_typing(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_typing',
            'user': event['user'],
        }))

    async def message_new(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message_new',
            'message': event['message'],
            'user': event['user'],
        }))