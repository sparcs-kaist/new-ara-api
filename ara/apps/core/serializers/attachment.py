from rest_framework import serializers

from apps.core.models import Attachment


class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = '__all__'
        read_only_fields = (
            'name',
            'created_at',
            'updated_at',
            'deleted_at',
        )
