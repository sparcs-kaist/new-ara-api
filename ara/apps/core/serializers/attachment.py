from ara.classes.serializers import MetaDataModelSerializer

from apps.core.models import Attachment


class BaseAttachmentSerializer(MetaDataModelSerializer):
    class Meta:
        model = Attachment
        fields = '__all__'
        read_only_fields = (
            'name',
        )


class AttachmentSerializer(BaseAttachmentSerializer):
    pass
