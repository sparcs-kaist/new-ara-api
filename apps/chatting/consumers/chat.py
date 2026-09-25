from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
import json

from apps.chatting.realtime import room_group_name

# 채팅 관련 Socket 을 핸들링하는 Consumer 클래스
class ChatRoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.room_name = None
        self.room_id = None
        self.identity = None

    async def disconnect(self, close_code):
        if self.room_name:
            await self.channel_layer.group_discard(self.room_name, self.channel_name)
            # 필요하면 user_leave 등 이벤트를 방에 알림

    # Helper: room group name
    def _group(self, room_id: int) -> str:
        return room_group_name(room_id)

    # 익명 방이면 user id 를 내보내지 않는다
    @database_sync_to_async
    def get_member_identity(self, room_id):
        from apps.chatting.models import ChatRoomMemberShip, ChatUserRole
        from apps.chatting.models.room import ChatNameType

        user = self.scope.get("user")
        if not user or not getattr(user, "is_authenticated", False):
            return None
        membership = ChatRoomMemberShip.objects.filter(
            chat_room_id=room_id,
            user=user,
        ).exclude(
            role__in=[ChatUserRole.BLOCKED.value, ChatUserRole.BLOCKER.value],
        ).select_related("chat_room", "user__profile").first()
        if membership is None:
            return None

        is_anonymous = membership.chat_room.chat_name_type == ChatNameType.ANONYMOUS.value
        return {
            "user": None if is_anonymous else user.id,
            "sender": {
                "display_name": membership.get_display_name(),
                "anon_number": membership.anon_number,
            },
        }

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
        #메시지 삭제 처리
        if event_type == "message_deleted":
            await self.broadcast_message_deleted(data.get('message_id'))
            return

        #상대방이 메시지를 타이핑 시작했을때 (보낸 사람은 서버가 채운다)
        if event_type == 'typing_start':
            await self.typing_start()
            return

        #상대방이 메시지 타이핑을 종료했을 때
        if event_type == 'typing_stop':
            await self.typing_stop()
            return

        # Legacy protocol (backward compatibility)
        if event_type == 'connect_room':
            await self.join(data['room_id'])
        elif event_type == 'disconnect_room':
            await self.leave(data['room_id'])
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
        identity = await self.get_member_identity(room_id)
        if identity is None:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'code': 'forbidden',
                'room_id': room_id,
            }))
            return

        # 기존에 접속한 방 있으면 나가기
        if self.room_name:
            await self.channel_layer.group_discard(self.room_name, self.channel_name)
        self.room_name = self._group(room_id)
        self.room_id = room_id
        self.identity = identity
        await self.channel_layer.group_add(self.room_name, self.channel_name)

        # 방에 접속한 걸 알림 (user_join)
        await self.channel_layer.group_send(
            self.room_name,
            {
                'type': 'user_join',
                **identity,
                'room_id': room_id,
            }
        )

    async def leave(self, room_id):
        # 들어가 있는 방만 나갈 수 있다 (남의 방에 user_leave 를 뿌리지 못하게)
        room_name = self._group(room_id)
        if self.room_name != room_name:
            return
        await self.channel_layer.group_discard(room_name, self.channel_name)

        await self.channel_layer.group_send(
            room_name,
            {
                'type': 'user_leave',
                **self.identity,
                'room_id': room_id,
            }
        )
        self.room_name = None
        self.room_id = None
        self.identity = None

    async def broadcast_update(self, payload: dict | None = None):
        """클라이언트 요청(message_new)을 처리하고 그룹으로 브로드캐스트"""
        if not self.room_name:
            return
        await self.channel_layer.group_send(
            self.room_name,
            {
                'type': 'room_update',
                'payload': payload or {},
            }
        )

    async def broadcast_message_deleted(self, message_id : int):
        """ 클라이언트 요청(message_deleted)을 처리하고 그룹으로 브로드캐스트"""
        if not self.room_name:
            return
        await self.channel_layer.group_send(
            self.room_name,
            {
                'type' : 'message_deleted',
                'message_id': message_id
            }
        )

    # 타이핑 시작 이벤트 처리 (브로드캐스트)
    async def typing_start(self):
        if not self.room_name:
            return
        await self.channel_layer.group_send(
            self.room_name,
            {
                'type': 'user_typing_start',
                **self.identity,
            }
        )

    # 타이핑 정지 이벤트 처리 (브로드캐스트)
    async def typing_stop(self):
        if not self.room_name:
            return
        await self.channel_layer.group_send(
            self.room_name,
            {
                'type': 'user_typing_stop',
                **self.identity,
            }
        )

    # 그룹에서 이벤트 받는 핸들러들
    async def user_join(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_join',
            'user': event.get('user'),
            'sender': event.get('sender'),
            'room_id': event.get('room_id'),
        }))

    async def user_leave(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_leave',
            'user': event.get('user'),
            'sender': event.get('sender'),
            'room_id': event.get('room_id'),
        }))

    async def user_typing_start(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_typing_start',
            'user': event.get('user'),
            'sender': event.get('sender'),
        }))

    async def user_typing_stop(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_typing_stop',
            'user': event.get('user'),
            'sender': event.get('sender'),
        }))

    async def message_deleted(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message_deleted',
            'message_id': event.get('message_id'),
        }))

    async def member_removed(self, event):
        if not self.identity or self.identity["sender"]["anon_number"] != event.get("anon_number"):
            return
        await self.channel_layer.group_discard(self.room_name, self.channel_name)
        await self.send(text_data=json.dumps({'type': 'removed', 'room_id': self.room_id}))
        self.room_name = None
        self.room_id = None
        self.identity = None

    async def room_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'room_update',
            'payload': event.get('payload', {}),
        }))

    # Backward-compat: if any producer still emits message_new to the group,
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
        }))
