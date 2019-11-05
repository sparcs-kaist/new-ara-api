from ara.classes.serializers import MetaDataModelSerializer

from apps.core.models import Report
from apps.core.serializers.article import ArticleListActionSerializer
from apps.core.serializers.comment import CommentListActionSerializer
from apps.user.serializers.user import PublicUserSerializer


class BaseReportSerializer(MetaDataModelSerializer):
    class Meta:
        model = Report
        fields = '__all__'


class ReportSerializer(BaseReportSerializer):
    parent_article = ArticleListActionSerializer(
        read_only=True,
    )

    parent_comment = CommentListActionSerializer(
        read_only=True,
    )

    reported_by = PublicUserSerializer(
        read_only=True,
    )


class ReportCreateActionSerializer(BaseReportSerializer):
    class Meta(BaseReportSerializer.Meta):
        read_only_fields = (
            'reported_by',
        )
