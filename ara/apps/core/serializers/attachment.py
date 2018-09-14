from ara.classes.serializers import MetaDataModelSerializer

from apps.core.models import Attachment


class AttachmentSerializer(MetaDataModelSerializer):
    class Meta:
        model = Attachment
        fields = '__all__'
        read_only_fields = (
            'name',
        )
