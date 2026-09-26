from rest_framework import routers
from apps.meal.views import meal_viewset, menu_photo_viewset, restaurant_viewset

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
