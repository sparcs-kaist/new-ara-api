from ara.classes.serializers import MetaDataModelSerializer

from apps.core.models import Attachment


class BaseAttachmentSerializer(MetaDataModelSerializer):
    class Meta:
        model = Attachment
        fields = '__all__'


class AttachmentSerializer(BaseAttachmentSerializer):
    pass
