from apps.core.models import Attachment
from ara.classes.serializers import MetaDataModelSerializer


class BaseAttachmentSerializer(MetaDataModelSerializer):
    class Meta:
        model = Attachment
        fields = "__all__"


class AttachmentSerializer(BaseAttachmentSerializer):
    pass
