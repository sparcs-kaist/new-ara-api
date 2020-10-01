from ara.classes.serializers import MetaDataModelSerializer

from apps.core.models import BestSearch


class BaseBestSearchSerializer(MetaDataModelSerializer):
    class Meta:
        model = BestSearch
        fields = '__all__'


class BestSearchSerializer(BaseBestSearchSerializer):
    pass
