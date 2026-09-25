from rest_framework import serializers

from apps.chatting.models.room import ChatRoom
from apps.chatting.models.vote import ChatVote
from apps.chatting.serializers.member import member_summary


class ChatVoteSerializer(serializers.ModelSerializer):
    # can_see_* 가 False 면 값은 null
    message_id = serializers.IntegerField(read_only=True)
    chat_room = serializers.IntegerField(source="message.chat_room_id", read_only=True)
    options = serializers.SerializerMethodField()
    voter_count = serializers.SerializerMethodField()
    my_option_ids = serializers.SerializerMethodField()

    class Meta:
        model = ChatVote
        fields = [
            'id', 'message_id', 'chat_room', 'title', 'max_choices',
            'options', 'voter_count', 'my_option_ids', 'created_at',
        ]

    def get_viewer(self):
        request = self.context.get("request")
        return request.user if request else None

    def get_options(self, obj):
        viewer = self.get_viewer()
        see_counts = obj.can_see_counts(viewer)
        see_voters = obj.can_see_voters(viewer)
        chat_room = obj.message.chat_room

        result = []
        for option in obj.options.all():
            ballots = list(option.ballots.all())
            result.append({
                "id": option.id,
                "text": option.text,
                "vote_count": len(ballots) if see_counts else None,
                "voters": [
                    member_summary(self, chat_room, ballot.user_id) for ballot in ballots
                ] if see_voters else None,
            })
        return result

    def get_voter_count(self, obj):
        if not obj.can_see_counts(self.get_viewer()):
            return None
        return len({
            ballot.user_id for option in obj.options.all() for ballot in option.ballots.all()
        })

    def get_my_option_ids(self, obj):
        viewer = self.get_viewer()
        if viewer is None:
            return []
        return [
            option.id for option in obj.options.all()
            if any(ballot.user_id == viewer.id for ballot in option.ballots.all())
        ]


class ChatVoteCreateSerializer(serializers.Serializer):
    chat_room = serializers.PrimaryKeyRelatedField(queryset=ChatRoom.objects.all())
    title = serializers.CharField(max_length=100)
    options = serializers.ListField(
        child=serializers.CharField(max_length=100),
        min_length=2,
        max_length=20,
    )
    max_choices = serializers.IntegerField(min_value=1, allow_null=True, required=False, default=1)

    def validate_options(self, value):
        stripped = [text.strip() for text in value]
        if any(not text for text in stripped):
            raise serializers.ValidationError("빈 선택지가 있습니다.")
        if len(set(stripped)) != len(stripped):
            raise serializers.ValidationError("중복된 선택지가 있습니다.")
        return stripped

    def validate(self, attrs):
        max_choices = attrs.get("max_choices")
        if max_choices is not None and max_choices > len(attrs["options"]):
            raise serializers.ValidationError("최대 선택 수가 선택지 수보다 많습니다.")
        return attrs


class ChatVoteCastSerializer(serializers.Serializer):
    option_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=True)
