from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend

from meal.models import MenuAllergy
from meal.serializers import MenuAllergySerializer

class MenuAllergyViewSet(viewsets.ModelViewSet):
    queryset = MenuAllergy.objects.all()
    serializer_class = MenuAllergySerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["menu_id", "cafeteria_menu_id", "allergen_code"]
