from rest_framework import serializers
from apps.chatting.models.room_invitation import ChatRoomInvitation
from apps.chatting.models.membership_room import ChatUserRole
from apps.user.serializers.user import PublicUserSerializer
from datetime import timedelta
from django.utils import timezone


class ChatInvitationSerializer(serializers.ModelSerializer):
    """
    초대장 조회용 시리얼라이저
    """
    invitation_from_data = PublicUserSerializer(source='invitation_from', read_only=True)
    invitation_to_data = PublicUserSerializer(source='invitation_to', read_only=True)

    class Meta:
        model = ChatRoomInvitation
        fields = [
            'id', 'invited_room', 'invitation_to', 'invitation_from',
            'invitation_role', 'expired_at', 'created_at',
            'invitation_from_data', 'invitation_to_data'
        ]
        read_only_fields = ['created_at']


class ChatInvitationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatRoomInvitation
        fields = [
            'invited_room',
            'invitation_to'
        ]

    def create(self, validated_data):
        validated_data['invitation_from'] = self.context['request'].user
        validated_data['invitation_role'] = ChatUserRole.PARTICIPANT.value
        validated_data['expired_at'] = timezone.now() + timedelta(days=7)

        return super().create(validated_data)

    def validate(self, attrs):
        invitation_to = attrs.get('invitation_to')
        invited_room = attrs.get('invited_room')

        if ChatRoomInvitation.objects.filter(
            invitation_to=invitation_to,
            invited_room=invited_room,
        ).exists():
            raise serializers.ValidationError("이미 초대한 사용자입니다.")

        if invited_room.membership_info_set.filter(user=invitation_to).exists():
            raise serializers.ValidationError("이미 참여 중인 사용자입니다.")

        return attrs