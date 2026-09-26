import re

from rest_framework import serializers

from apps.meal.models import WEEKDAYS, Store, StoreEvent, StoreEventKind, StoreMenu, StoreNotice

TIME_RX = re.compile(r"^([01]\d|2[0-4]):[0-5]\d$")


class OpenStateMixin:
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.update(instance.open_state())
        return data


class StoreListSerializer(OpenStateMixin, serializers.ModelSerializer):
    signature_menus = serializers.SerializerMethodField()

    class Meta:
        model = Store
        fields = [
            "id", "name", "zone", "location", "hours", "hours_note", "cover", "restaurant",
            "is_active", "signature_menus",
        ]

    def get_signature_menus(self, obj):
        menus = getattr(obj, "signature_list", None)
        if menus is None:
            menus = obj.menus.filter(is_signature=True)
        return [menu.name for menu in menus][:3]


class StoreMenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreMenu
        fields = ["id", "section", "name", "price", "description", "photo", "is_sold_out", "is_signature", "order"]


class StoreNoticeSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreNotice
        fields = ["id", "title", "body", "starts_at", "ends_at", "created_at"]


class StoreEventSerializer(serializers.ModelSerializer):
    open = serializers.TimeField(source="open_time", format="%H:%M", required=False, allow_null=True)
    close = serializers.TimeField(source="close_time", format="%H:%M", required=False, allow_null=True)

    class Meta:
        model = StoreEvent
        fields = ["id", "kind", "starts_at", "ends_at", "reason", "open", "close"]

    def validate(self, attrs):
        merged = {**{f: getattr(self.instance, f) for f in ("kind", "starts_at", "ends_at", "open_time", "close_time")}, **attrs} \
            if self.instance else attrs
        if merged.get("ends_at") and merged["ends_at"] < merged["starts_at"]:
            raise serializers.ValidationError({"detail": "끝이 시작보다 빨라요."})
        if merged.get("kind") == StoreEventKind.OPEN.value:
            if not merged.get("open_time") or not merged.get("close_time"):
                raise serializers.ValidationError({"detail": "임시 영업은 open, close 시간이 필요해요."})
            if merged["open_time"] >= merged["close_time"]:
                raise serializers.ValidationError({"detail": "영업 시작이 끝보다 늦어요."})
        return attrs


class StoreDetailSerializer(StoreListSerializer):
    menus = StoreMenuSerializer(many=True, read_only=True)
    notices = serializers.SerializerMethodField()
    events = serializers.SerializerMethodField()
    is_staff = serializers.SerializerMethodField()

    class Meta(StoreListSerializer.Meta):
        fields = StoreListSerializer.Meta.fields + ["intro", "phone", "link", "menus", "notices", "events", "is_staff"]

    def get_notices(self, obj):
        return StoreNoticeSerializer(obj.active_notices(), many=True).data

    def get_events(self, obj):
        return StoreEventSerializer(obj.current_events, many=True).data

    def get_is_staff(self, obj):
        request = self.context.get("request")
        return obj.is_staff(request.user) if request else False


def validate_hours_value(value):
    if not isinstance(value, dict) or set(value) - set(WEEKDAYS):
        raise serializers.ValidationError(f"요일 키는 {', '.join(WEEKDAYS)} 만 쓸 수 있어요.")
    for day, blocks in value.items():
        if not isinstance(blocks, list):
            raise serializers.ValidationError(f"{day} 는 구간 목록이어야 해요.")
        for block in blocks:
            open_at, close_at = (block or {}).get("open", ""), (block or {}).get("close", "")
            if not (TIME_RX.match(open_at) and TIME_RX.match(close_at)) or open_at >= close_at:
                raise serializers.ValidationError(f"{day} 의 시간은 HH:MM 이고 open 이 close 보다 빨라야 해요.")
    return value


# 직원이 고칠 수 있는 업체 정보 (운영 여부 / 식당 연결 / 정렬은 운영진만)
class StoreUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ["name", "zone", "intro", "location", "hours", "hours_note", "cover", "phone", "link"]

    def validate_hours(self, value):
        return validate_hours_value(value)
