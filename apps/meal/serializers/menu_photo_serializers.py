from rest_framework import serializers

from apps.meal.models import MealType, MenuPhoto, Restaurant


class MenuPhotoSerializer(serializers.ModelSerializer):
    restaurant = serializers.SerializerMethodField()
    is_official = serializers.BooleanField(read_only=True)
    author = serializers.SerializerMethodField()
    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = MenuPhoto
        fields = [
            'id', 'restaurant', 'date', 'meal_time', 'image', 'comment',
            'is_official', 'source', 'author', 'is_mine', 'created_at',
        ]

    def get_restaurant(self, obj):
        return {"id": obj.restaurant_id, "name": obj.restaurant.restaurant_name}

    def get_author(self, obj):
        profile = getattr(obj.created_by, "profile", None) if obj.created_by_id else None
        return {"nickname": profile.nickname} if profile else None

    def get_is_mine(self, obj):
        request = self.context.get("request")
        return bool(request and request.user.is_authenticated and obj.created_by_id == request.user.id)


class MenuPhotoCreateSerializer(serializers.Serializer):
    restaurant_id = serializers.PrimaryKeyRelatedField(queryset=Restaurant.objects.all(), source="restaurant")
    # YYYYMMDD (식단 조회 API 와 같은 형식)
    date = serializers.DateField(input_formats=["%Y%m%d"])
    meal_time = serializers.ChoiceField(choices=[meal_type.value for meal_type in MealType])
    image = serializers.ImageField()
    comment = serializers.CharField(max_length=200, required=False, allow_blank=True, default="")
