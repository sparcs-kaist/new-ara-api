from rest_framework import serializers

from apps.core.models.board_group import BoardGroup
from apps.core.serializers.board import SimpleBoardSerializer


class BoardGroupSerializer(serializers.ModelSerializer):
    boards = SimpleBoardSerializer(many=True, read_only=True)

    class Meta:
        model = BoardGroup
        fields = ["id", "slug", "ko_name", "en_name", "boards"]
        depth = 1
