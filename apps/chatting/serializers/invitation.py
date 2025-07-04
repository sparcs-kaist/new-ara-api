from rest_framework import serializers
from apps.chatting.models.room_invitation import ChatRoomInvitation
from apps.user.serializers.user import UserSerializer


class ChatRoomInvitationSerializer(serializers.ModelSerializer):
    """
    초대장 조회용 시리얼라이저
    """
    invitation_from_data = UserSerializer(source='invitation_from', read_only=True)
    invitation_to_data = UserSerializer(source='invitation_to', read_only=True)
    
    class Meta:
        model = ChatRoomInvitation
        fields = [
            'id', 'invited_room', 'invitation_to', 'invitation_from',
            'invitation_role', 'expired_at', 'created_at',
            'invitation_from_data', 'invitation_to_data'
        ]
        read_only_fields = ['created_at']


class ChatRoomInvitationCreateSerializer(serializers.ModelSerializer):
    """
    초대장 생성용 시리얼라이저
    """
    class Meta:
        model = ChatRoomInvitation
        fields = ['invited_room', 'invitation_to', 'invitation_role', 'expired_at']
    
    def create(self, validated_data):
        # 초대한 사람은 현재 로그인한 사용자
        validated_data['invitation_from'] = self.context['request'].user
        return super().create(validated_data)
    
    def validate(self, attrs):
        # 추가 유효성 검사
        invitation_to = attrs.get('invitation_to')
        invited_room = attrs.get('invited_room')
        
        # 이미 초대한 사용자인지 확인
        if ChatRoomInvitation.objects.filter(
            invitation_to=invitation_to,
            invited_room=invited_room
        ).exists():
            raise serializers.ValidationError("이미 초대한 사용자입니다.")
            
        # 이미 참여 중인 사용자인지 확인
        if invited_room.membership_info_set.filter(user=invitation_to).exists():
            raise serializers.ValidationError("이미 참여 중인 사용자입니다.")
            
        return attrs