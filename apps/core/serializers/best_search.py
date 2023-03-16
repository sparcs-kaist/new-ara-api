from apps.core.models import BestSearch
from ara.classes.serializers import MetaDataModelSerializer


class BaseBestSearchSerializer(MetaDataModelSerializer):
    class Meta:
        model = BestSearch
        fields = "__all__"


class BestSearchSerializer(BaseBestSearchSerializer):
    pass
