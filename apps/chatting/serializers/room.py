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
    
class ChatRoomSerializer(serializers.ModelSerializer):
    """
    채팅방 정보 조회용 Serializer
    """
    class Meta:
        model = ChatRoom
        fields = [
            'id', 'room_title', 'room_type', 'chat_name_type',
            'recent_message_at', 'recent_message'
        ]
        read_only_fields = ['recent_message_at', 'recent_message']

class ChatRoomByIdSerializer(serializers.Serializer):
    """
    채팅방 ID를 받아서 채팅방 객체를 반환하는 Serializer
    """
    room_id = serializers.IntegerField()
    
    def validate_room_id(self, value):
        try:
            # 입력받은 ID로 채팅방 객체 조회
            room = ChatRoom.objects.get(id=value)
            # validate_room_id 메서드의 반환값이 직렬화된 값이 됨
            return room
        except ChatRoom.DoesNotExist:
            raise serializers.ValidationError(f"ID가 {value}인 채팅방이 존재하지 않습니다.")
            
    def create(self, validated_data):
        # validated_data['room_id']는 이미 ChatRoom 객체임
        return validated_data['room_id']
        
    def to_representation(self, instance):
        # ChatRoom 객체를 반환할 때 사용할 시리얼라이저
        return ChatRoomSerializer(instance).data