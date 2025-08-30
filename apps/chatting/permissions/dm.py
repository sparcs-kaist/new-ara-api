from rest_framework import permissions
from apps.chatting.models.membership_room import ChatRoomMemberShip, ChatUserRole, ChatRoom, ChatRoomType
from django.db.models import Q
from django.contrib.auth import get_user_model

#DM 생성 권한 - 이미 만들어진 방이 없고, 차단 상태가 아닌 경우
class CreateDMPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        dm_to = request.data.get("dm_to")
        if not dm_to:   
            return False
        #두 User 사이에 이미 만들어진 DM 방이 있는지 확인
        existing_dm = ChatRoomMemberShip.is_dm_exist(request.user, dm_to)
        if existing_dm:
            return False
        return True

#DM 떠나기 권한 - 이미 방에 참여중, 차단 상태가 아닌 경우
#처음에는 DM방도 떠날 수 있게 하려고 했으나, DM은 방을 떠난다는 개념이 필요 없기에 deprecated함

"""
@deprecated
class LeaveDMPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        room = view.get_object()
        membership = ChatRoomMemberShip.objects.filter(
            chat_room=room,
            user=request.user
        ).first()

        # 참여 중인 방이면서 차단 상태가 아닌 경우
        return membership and membership.role not in [
            ChatUserRole.BLOCKED.value,
            ChatUserRole.BLOCKER.value,
        ]
""" 

#DM 차단 권한 - 사용자 ID 기반으로 확인
class BlockDMPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # payload에서 user_id 가져오기
        user_id = request.data.get('user_id')
        if not user_id:
            return False
        
        try:
            User = get_user_model()
            other_user = User.objects.get(id=user_id)
            
            # 자기 자신 차단 방지
            if other_user == request.user:
                return False
            
            # 두 사용자 간의 DM 방 찾기
            dm_rooms = ChatRoom.objects.filter(
                room_type=ChatRoomType.DM.value,
                membership_info_set__user=request.user
            ).filter(
                membership_info_set__user=other_user
            ).distinct()
            
            if dm_rooms.exists():
                dm_room = dm_rooms.first()
                
                # 내 멤버십 확인
                my_membership = ChatRoomMemberShip.objects.filter(
                    chat_room=dm_room,
                    user=request.user
                ).first()
                
                # 상대방 멤버십 확인
                other_membership = ChatRoomMemberShip.objects.filter(
                    chat_room=dm_room,
                    user=other_user
                ).first()
                
                # 내가 이미 차단 상태인 경우 차단 불가
                if my_membership and my_membership.role == ChatUserRole.BLOCKER.value:
                    return False
                
                # 상대방이 나를 차단한 상태인 경우 차단 불가
                if other_membership and other_membership.role == ChatUserRole.BLOCKER.value:
                    return False
                
                # 내가 이미 차단당한 상태인 경우 차단 불가
                if my_membership and my_membership.role == ChatUserRole.BLOCKED.value:
                    return False
                
                return True
            else:
                # DM 방이 없으면 차단 가능 (새로 생성)
                return True
                
        except User.DoesNotExist:
            return False
        except Exception:
            return False

#DM 차단 해제 권한 - 사용자 ID 기반으로 확인
class UnblockDMPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # payload에서 user_id 가져오기
        user_id = request.data.get('user_id')
        if not user_id:
            return False
        
        try:
            User = get_user_model()
            other_user = User.objects.get(id=user_id)
            
            # 두 사용자 간의 DM 방 찾기
            dm_rooms = ChatRoom.objects.filter(
                room_type=ChatRoomType.DM.value,
                membership_info_set__user=request.user
            ).filter(
                membership_info_set__user=other_user
            ).distinct()
            
            if dm_rooms.exists():
                dm_room = dm_rooms.first()
                
                # 내 멤버십 확인
                my_membership = ChatRoomMemberShip.objects.filter(
                    chat_room=dm_room,
                    user=request.user
                ).first()
                
                # 상대방 멤버십 확인
                other_membership = ChatRoomMemberShip.objects.filter(
                    chat_room=dm_room,
                    user=other_user
                ).first()
                
                # 내가 차단자인 경우에만 차단 해제 가능
                if my_membership and my_membership.role == ChatUserRole.BLOCKER.value:
                    return True
                
                # 상대방이 나를 차단한 상태에서는 차단 해제 불가
                if other_membership and other_membership.role == ChatUserRole.BLOCKER.value:
                    return False
                
                return False
            else:
                # DM 방이 없으면 차단 해제할 필요 없음
                return False
                
        except User.DoesNotExist:
            return False
        except Exception:
            return False
