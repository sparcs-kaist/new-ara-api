from apps.global_notice.models import GlobalNotice
from ara.classes.serializers.meta_data import MetaDataModelSerializer


class GlobalNoticeSerializer(MetaDataModelSerializer):
    class Meta:
        model = GlobalNotice
        fields = ["title", "content"]
