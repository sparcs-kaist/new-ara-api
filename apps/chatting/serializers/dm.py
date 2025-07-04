from rest_framework import serializers
from apps.chatting.models.room import ChatRoom, ChatRoomType
from apps.user.serializers.user import PublicUserSerializer
from django.contrib.auth import get_user_model

class DMSerializer(serializers.ModelSerializer):
    """
    DM 조회용 시리얼라이저
    """
    other_user = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatRoom
        fields = [
            'id', 'room_title', 'room_type', 'created_at', 'recent_message_at', 
            'recent_message', 'other_user'
        ]
        read_only_fields = ['room_type', 'created_at', 'recent_message_at', 'recent_message']
    
    def get_other_user(self, obj):
        """DM 상대방 정보 가져오기"""
        request = self.context.get('request')
        if not request:
            return None
            
        # 현재 사용자가 아닌 다른 멤버십 찾기
        other_membership = obj.membership_info_set.exclude(user=request.user).first()
        if not other_membership:
            return None
            
        return PublicUserSerializer(other_membership.user).data

class DMCreateSerializer(serializers.Serializer):
    """
    DM 생성용 시리얼라이저
    """
    dm_to = serializers.PrimaryKeyRelatedField(
        queryset=get_user_model().objects.all()
    )