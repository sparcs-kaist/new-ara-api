from rest_framework import serializers

from apps.meal.models import Store, StoreMenu, StoreNotice


class StoreListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ["id", "name", "zone", "location", "hours", "cover", "restaurant", "is_active"]


class StoreMenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreMenu
        fields = ["id", "section", "name", "price", "description", "photo", "is_sold_out", "order"]


class StoreNoticeSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreNotice
        fields = ["id", "title", "body", "starts_at", "ends_at", "created_at"]


class StoreDetailSerializer(StoreListSerializer):
    menus = StoreMenuSerializer(many=True, read_only=True)
    notices = serializers.SerializerMethodField()
    is_staff = serializers.SerializerMethodField()

    class Meta(StoreListSerializer.Meta):
        fields = StoreListSerializer.Meta.fields + ["intro", "phone", "link", "menus", "notices", "is_staff"]

    def get_notices(self, obj):
        return StoreNoticeSerializer(obj.active_notices(), many=True).data

    def get_is_staff(self, obj):
        request = self.context.get("request")
        return obj.is_staff(request.user) if request else False


# 직원이 고칠 수 있는 업체 정보 (이름 / 구역 / 운영 여부는 운영진이 admin 에서)
class StoreUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ["intro", "location", "hours", "cover", "phone", "link"]
