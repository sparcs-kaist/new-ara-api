from rest_framework import serializers

from .models import Calendar, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["name", "color"]


class CalendarSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)

    class Meta:
        model = Calendar
        fields = "__all__"


class RecursiveTagSerializer(serializers.Serializer):
    def to_representation(self, value):
        serializer = TagSerializer(value, context=self.context)
        return serializer.data


class RecursiveCalendarSerializer(serializers.Serializer):
    def to_representation(self, value):
        serializer = CalendarSerializer(value, context=self.context)
        return serializer.data


class TagSerializer(serializers.ModelSerializer):
    calendars = RecursiveCalendarSerializer(many=True)

    class Meta:
        model = Tag
        fields = ["name", "color", "calendars"]
