from channels.generic.websocket import AsyncWebsocketConsumer
import json

# 채팅 관련 Socket 을 핸들링하는 Consumer 클래스
class ChatRoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.room_name = None

    async def disconnect(self, close_code):
        if self.room_name:
            await self.channel_layer.group_discard(self.room_name, self.channel_name)
            # 필요하면 user_leave 등 이벤트를 방에 알림

    # Helper: room group name
    def _group(self, room_id: int) -> str:
        return f"chat_{room_id}"

    # Helper: lightweight user identity for broadcasts
    def _user_identity(self):
        user = self.scope.get("user")
        if user and getattr(user, "is_authenticated", False):
            return getattr(user, "id", self.channel_name)
        return self.channel_name

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        event_type = data.get('type')

        # New protocol
        if event_type == 'join':
            await self.join(data['room_id'])
            return
        if event_type == 'leave':
            await self.leave(data['room_id'])
            return
        if event_type == 'update':
            await self.broadcast_update(data.get('payload', {}))
            return

        # Legacy protocol (backward compatibility)
        if event_type == 'connect_room':
            await self.join(data['room_id'])
        elif event_type == 'disconnect_room':
            await self.leave(data['room_id'])
        elif event_type == 'typing_start':
            await self.typing_start()
        elif event_type == 'message_new':
            # normalize to unified room_update payload
            msg = data.get('message')
            await self.broadcast_update({
                'resource': 'messages',
                'change': 'created',
                'data': msg,
                'room_id': msg.get('room_id') if isinstance(msg, dict) else None,
            })
        # 여기에 더 필요한 이벤트 타입 추가

    async def join(self, room_id):
        # 기존에 접속한 방 있으면 나가기
        if self.room_name:
            await self.channel_layer.group_discard(self.room_name, self.channel_name)
        self.room_name = self._group(room_id)
        await self.channel_layer.group_add(self.room_name, self.channel_name)

        # 방에 접속한 걸 알림 (user_join)
        await self.channel_layer.group_send(
            self.room_name,
            {
                'type': 'user_join',
                'user': self._user_identity(),  # 실제론 유저 id 등
                'room_id': room_id,
            }
        )

    async def leave(self, room_id):
        room_name = self._group(room_id)
        await self.channel_layer.group_discard(room_name, self.channel_name)

        await self.channel_layer.group_send(
            room_name,
            {
                'type': 'user_leave',
                'user': self._user_identity(),
                'room_id': room_id,
            }
        )

    
        # If leaving current room, clear it
        if self.room_name == room_name:
            self.room_name = None

    async def typing_start(self):
        # typing_start 이벤트를 그룹에 브로드캐스트
        if not self.room_name:
            return
        await self.channel_layer.group_send(
            self.room_name,
            {
                'type': 'user_typing',
                'user': self._user_identity(),
            }
        )

    async def broadcast_update(self, payload: dict | None = None):
        """클라이언트 요청(message_new)을 처리하고 그룹으로 브로드캐스트"""
        if not self.room_name:
            return
        await self.channel_layer.group_send(
            self.room_name,
            {
                'type': 'room_update',
                'payload': payload or {},
                'user': self._user_identity(),
            }
        )

    # Deprecated: kept for compatibility; delegate to unified room_update
    async def broadcast_message_new(self, message):
        await self.broadcast_update({
            'resource': 'messages',
            'change': 'created',
            'data': message,
            'room_id': message.get('room_id') if isinstance(message, dict) else None,
        })

    # 그룹에서 이벤트 받는 핸들러들
    async def user_join(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_join',
            'user': event['user'],
            'room_id': event.get('room_id'),
        }))

    async def user_leave(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_leave',
            'user': event['user'],
            'room_id': event.get('room_id'),
        }))

    async def user_typing(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_typing',
            'user': event['user'],
        }))

    async def room_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'room_update',
            'payload': event.get('payload', {}),
            'user': event.get('user'),
        }))

    # Backward-compat: if any producer still emits message_new to the group,
    # convert it to unified room_update for clients
    async def message_new(self, event):
        msg = event.get('message')
        await self.send(text_data=json.dumps({
            'type': 'room_update',
            'payload': {
                'resource': 'messages',
                'change': 'created',
                'data': msg,
                'room_id': msg.get('room_id') if isinstance(msg, dict) else None,
            },
            'user': event.get('user'),
        }))

