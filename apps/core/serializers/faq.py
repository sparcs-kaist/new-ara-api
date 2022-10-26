from apps.core.models.faq import FAQ
from ara.classes.serializers import MetaDataModelSerializer


class BaseFAQSerializer(MetaDataModelSerializer):
    class Meta:
        model = FAQ
        fields = "__all__"


class FAQSerializer(BaseFAQSerializer):
    pass
