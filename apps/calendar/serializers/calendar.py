from calendar.models import Calendar, Tag

from rest_framework import serializers


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "calendar"]


class CalendarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Calendar
        fields = [
            "id",
            "is_allday",
            "start_at",
            "end_at",
            "ko_title",
            "en_title",
            "tags",
        ]
