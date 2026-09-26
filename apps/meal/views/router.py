from rest_framework import routers
from apps.meal.views import meal_viewset, menu_photo_viewset, ops_viewset, restaurant_viewset, store_viewset

router = routers.DefaultRouter()

router.register(
    prefix=r"meal",
    viewset=meal_viewset.MealViewSet,
    basename="meal",
)

router.register(
    prefix=r"meal/photos",
    viewset=menu_photo_viewset.MenuPhotoViewSet,
    basename="meal_photo",
)

router.register(
    prefix=r"meal/restaurants",
    viewset=restaurant_viewset.RestaurantViewSet,
    basename="meal_restaurant",
)

router.register(
    prefix=r"stores",
    viewset=store_viewset.StoreViewSet,
    basename="store",
)

# 운영진(is_staff) 전용 식사 탭 관리. api/admin/ 은 Django admin 이라 ops 로 둔다
router.register(prefix=r"ops/stores", viewset=ops_viewset.OpsStoreViewSet, basename="ops_store")
router.register(prefix=r"ops/restaurants", viewset=ops_viewset.OpsRestaurantViewSet, basename="ops_restaurant")
router.register(prefix=r"ops/users", viewset=ops_viewset.OpsUserViewSet, basename="ops_user")
