from calendar.models import Calendar, Tag

from rest_framework import serializers


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["name", "color", "calendar"]


class CalendarSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)

    class Meta:
        model = Calendar
        fields = "__all__"
