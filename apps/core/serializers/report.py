from django.db import IntegrityError
from django.utils.translation import gettext
from rest_framework import serializers

from ara.classes.serializers import MetaDataModelSerializer

from apps.core.models import Report


class BaseReportSerializer(MetaDataModelSerializer):
    class Meta:
        model = Report
        fields = '__all__'


class ReportSerializer(BaseReportSerializer):
    from apps.core.serializers.article import ArticleListActionSerializer
    parent_article = ArticleListActionSerializer(
        read_only=True,
    )

    from apps.core.serializers.comment import CommentListActionSerializer
    parent_comment = CommentListActionSerializer(
        read_only=True,
    )

    from apps.user.serializers.user import PublicUserSerializer
    reported_by = PublicUserSerializer(
        read_only=True,
    )


class ReportCreateActionSerializer(BaseReportSerializer):
    class Meta(BaseReportSerializer.Meta):
        read_only_fields = (
            'reported_by',
        )

    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except IntegrityError:
            raise serializers.ValidationError(gettext("You already reported this article."))
