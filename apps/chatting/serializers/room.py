from rest_framework import serializers
from apps.chatting.models.room import ChatRoom, ChatRoomType
from apps.chatting.models.membership_room import ChatRoomMemberShip, ChatUserRole
from apps.chatting.models.room_permission import ChatRoomPermission

class ChatRoomCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatRoom
        fields = ['room_title', 'room_type', 'chat_name_type']
    
    def create(self, validated_data):
        # 1. 채팅방 생성
        room = ChatRoom.objects.create(**validated_data)
        
        # @Todo : 채팅방이 오픈 채팅일 경우 권한 설정 Option에 따라 Permission 만들기
        # 여기서 오픈채팅, 그룹채팅에 따라 다른 기본 권한을 설정할 수 있음
        # 그룹 채팅의 기본 권한 설정
        ChatRoomPermission.objects.create(
            chat_room=room,
            entrance_permission="INVITATION",  # 초대로만 입장 가능
            invite_permission="PARTICIPANT",  # 참여자 이상 초대 가능
            message_permission="PARTICIPANT",  # 참여자 이상 메시지 보내기 가능
            # 기타 필요한 권한 설정
        )

        #채팅방 생성자는 membership_room 에 OWNER로 추가하기
        ChatRoomMemberShip.objects.create(
            chat_room=room,
            user=self.context['request'].user,
            role=ChatUserRole.OWNER.value
        )

        return room
    
    def validate(self, attrs):
        # 추가 유효성 검사 (예: 타입에 따른 필수 필드 등)
        if attrs.get('room_type') == ChatRoomType.DM.value:
            # DM은 별도 엔드포인트에서 처리한다고 했으므로 에러 발생
            raise serializers.ValidationError(
                "DM 채팅방은 이 엔드포인트로 생성할 수 없습니다. 'chat/dm/create'를 이용하세요."
            )
        
        # 채팅방 제목이 필요한 경우에만 검증
        if attrs.get('room_type') in [ChatRoomType.GROUP_DM.value, ChatRoomType.OPEN_CHAT.value]:
            if not attrs.get('room_title'):
                raise serializers.ValidationError("그룹/오픈 채팅방은 제목이 필요합니다.")
        
        return attrs