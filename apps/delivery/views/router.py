from rest_framework import routers
from apps.delivery.views import delivery_viewset

router = routers.DefaultRouter()

router.register(
    prefix=r"delivery",
    viewset=delivery_viewset.DeliveryPartyViewSet,
    basename="delivery",
)
