from rest_framework import (
    decorators,
    permissions,
    response,
    serializers,
    status,
    viewsets,
)
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from django.db.models import Q
from django.db import IntegrityError

from drf_spectacular.utils import extend_schema, extend_schema_view

from django.utils import timezone

from ara.classes.viewset import ActionAPIViewSet
from apps.chatting.models.room import ChatRoom, ChatRoomType
from apps.chatting.models.membership_room import ChatRoomMemberShip, ChatUserRole
from apps.chatting.serializers.dm import (
    DMCreateSerializer, 
    DMSerializer, 
    DMBlockSerializer, 
    DMActionResponseSerializer
)
from apps.chatting.permissions.dm import (
    CreateDMPermission,
    BlockDMPermission,
    UnblockDMPermission,
)

import random

#랜덤 프로필 사진 지정 함수
#일단은 적당한 asset이 아직 만들어지지 않은 관계로 기존의 UserProfile과 동일하게 사용
def get_default_chatroom_picture() -> str:
    colors = ["blue", "red", "gray"]
    numbers = ["1", "2", "3"]

    col = random.choice(colors)
    num = random.choice(numbers)
    return f"user_profiles/default_pictures/{col}-default{num}.png"


@extend_schema_view(
    update=extend_schema(exclude=True),
    partial_update=extend_schema(exclude=True),
    retrieve=extend_schema(exclude=True),
    destroy=extend_schema(exclude=True),
    block=extend_schema(
        request=DMBlockSerializer,
        responses={200: DMActionResponseSerializer},
        description="사용자 ID로 DM 차단하기."
    ),
    unblock=extend_schema(
        request=DMBlockSerializer,
        responses={200: DMActionResponseSerializer},
        description="사용자 ID로 DM 차단 해제하기."
    )
)
class DMViewSet(viewsets.ModelViewSet, ActionAPIViewSet):
    http_method_names = ['get', 'post']  # patch 제거
    queryset = ChatRoom.objects.filter(room_type=ChatRoomType.DM.value)
    serializer_class = DMSerializer
    
    action_permission_classes = {
        "list": (permissions.IsAuthenticated,),
        "create": (permissions.IsAuthenticated, CreateDMPermission,),
        "block": (permissions.IsAuthenticated, BlockDMPermission,),  # 권한 추가
        "unblock": (permissions.IsAuthenticated, UnblockDMPermission,),  # 권한 추가
    }
    
    action_serializer_class = {
        "create": DMCreateSerializer,
        "block": DMBlockSerializer,
        "unblock": DMBlockSerializer,
    }

    def get_object(self):
        # get_object() 메서드를 원래대로 복원
        # 모든 액션에서 기본 동작 사용
        return super().get_object()

    def get_queryset(self):
        # DM 목록 조회 시 자신이 참여한 DM만 조회
        if self.request.method == "GET":
            return ChatRoom.objects.filter(
                room_type=ChatRoomType.DM.value,
                membership_info_set__user=self.request.user
            ).distinct()
        return super().get_queryset()
    
    # dm/ POST: DM 방 만들기 - 기존 메서드 활용
    def create(self, request, *args, **kwargs):
        # 이미 존재하는 DM인 경우 : permission에서 block
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # 대화 상대 ID
        dm_to = serializer.validated_data['dm_to']
        
        # 새 DM 생성
        user_nickname = request.user.profile.nickname
        dm_to_nickname = dm_to.profile.nickname

        # 요청에 picture가 있으면 사용, 없으면 기본 프사
        picture = request.data.get('picture') or get_default_chatroom_picture()

        dm_room = ChatRoom.objects.create(
            room_type=ChatRoomType.DM.value,
            room_title=f"DM_{user_nickname},{dm_to_nickname}",
            picture=picture,
        )
        
        # 두 사용자 모두 참가자로 추가
        ChatRoomMemberShip.objects.create(
            chat_room=dm_room, 
            user=request.user, 
            role=ChatUserRole.PARTICIPANT.value
        )
        
        ChatRoomMemberShip.objects.create(
            chat_room=dm_room, 
            user=dm_to, 
            role=ChatUserRole.PARTICIPANT.value
        )
        
        return response.Response(
            DMSerializer(dm_room, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )
    
    # dm/ DELETE: DM 방 나가기 : 로직상 지원 X (DM은 방을 나간다는 개념이 없음)
    
    # dm/block PATCH: DM 차단하기 - block_dm 메서드 활용
    @action(detail=False, methods=["post"])
    def block(self, request):
        # 권한은 이미 BlockDMPermission에서 확인했으므로 바로 진행
        serializer = DMBlockSerializer(data=request.data)
        if not serializer.is_valid():
            return response.Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user_id = serializer.validated_data['user_id']
        
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            other_user = User.objects.get(id=user_id)
            
            # 이미 존재하는 DM 방 찾기
            dm_rooms = ChatRoom.objects.filter(
                room_type=ChatRoomType.DM.value,
                membership_info_set__user_id=request.user.id
            ).filter(
                membership_info_set__user_id=other_user.id
            ).distinct()
            
            if dm_rooms.exists():
                # 기존 DM 방이 있으면 차단 처리
                dm_room = dm_rooms.first()
                
                # 내 멤버십 찾기/업데이트
                my_membership = dm_room.membership_info_set.filter(
                    user_id=request.user.id
                ).first()
                
                if my_membership:
                    my_membership.role = ChatUserRole.BLOCKER.value
                    my_membership.save()
                else:
                    ChatRoomMemberShip.objects.create(
                        chat_room=dm_room,
                        user=request.user,
                        role=ChatUserRole.BLOCKER.value
                    )
                
                # 상대방 멤버십 찾기/업데이트
                other_membership = dm_room.membership_info_set.filter(
                    user_id=other_user.id
                ).first()
                
                if other_membership:
                    other_membership.role = ChatUserRole.BLOCKED.value
                    other_membership.save()
            else:
                # DM 방이 없으면 새로 생성하고 차단 상태로 설정
                try:
                    user_nickname = request.user.profile.nickname
                    other_nickname = other_user.profile.nickname
                    dm_title = f"DM_{user_nickname},{other_nickname}"
                except:
                    dm_title = f"DM_{request.user.id}_{other_user.id}"
                    
                dm_room = ChatRoom.objects.create(
                    room_type=ChatRoomType.DM.value,
                    room_title=dm_title
                )
                
                # 두 사용자 모두 추가 (나는 차단자, 상대방은 차단됨)
                ChatRoomMemberShip.objects.create(
                    chat_room=dm_room,
                    user=request.user,
                    role=ChatUserRole.BLOCKER.value
                )
                
                ChatRoomMemberShip.objects.create(
                    chat_room=dm_room,
                    user=other_user,
                    role=ChatUserRole.BLOCKED.value
                )
                
            return response.Response(
                {"message": "차단되었습니다."},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return response.Response(
                {"message": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # dm/unblock PATCH: DM 차단 해제하기
    @action(detail=False, methods=["post"])
    def unblock(self, request):
        user_id = request.data.get('user_id')
        if not user_id:
            return response.Response(
                {"error": "차단 해제할 사용자 ID가 필요합니다."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            other_user = User.objects.get(id=user_id)
            
            # 기존 DM 방 찾기
            dm_rooms = ChatRoom.objects.filter(
                room_type=ChatRoomType.DM.value,
                membership_info_set__user_id=request.user.id
            ).filter(
                membership_info_set__user_id=other_user.id
            ).distinct()
            
            if dm_rooms.exists():
                dm_room = dm_rooms.first()
                
                # 멤버십 찾기
                my_membership = dm_room.membership_info_set.filter(
                    user_id=request.user.id
                ).first()
                
                other_membership = dm_room.membership_info_set.filter(
                    user_id=other_user.id
                ).first()
                
                # 차단 해제 처리
                if my_membership:
                    my_membership.role = ChatUserRole.PARTICIPANT.value
                    my_membership.save()
                
                if other_membership:
                    other_membership.role = ChatUserRole.PARTICIPANT.value
                    other_membership.save()

            return response.Response(status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return response.Response(
                {"error": "해당 사용자가 존재하지 않습니다."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return response.Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )