from rest_framework import serializers

from apps.calendar.models import Event


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = [
            "id",
            "is_all_day",
            "start_at",
            "end_at",
            "ko_title",
            "en_title",
            "ko_description",
            "en_description",
            "location",
            "url",
            "tags",
        ]
        depth = 1
