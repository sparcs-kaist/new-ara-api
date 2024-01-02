from apps.global_notice.models import GlobalNotice
from ara.classes.serializers.meta_data import MetaDataModelSerializer


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
