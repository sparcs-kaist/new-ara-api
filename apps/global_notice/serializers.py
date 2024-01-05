from ara.classes.serializers.meta_data import MetaDataModelSerializer

from .models import GlobalNotice


class GlobalNoticeSerializer(MetaDataModelSerializer):
    class Meta:
        model = GlobalNotice
        fields = [
            "ko_title",
            "en_title",
            "ko_content",
            "en_content",
            "started_at",
            "expired_at",
        ]
