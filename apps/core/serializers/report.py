from django.db import IntegrityError
from django.utils.translation import gettext
from rest_framework import serializers

from apps.core.models import Report
from ara.classes.serializers import MetaDataModelSerializer


class BaseReportSerializer(MetaDataModelSerializer):
    class Meta:
        model = Report
        fields = "__all__"


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

    class Meta(BaseReportSerializer.Meta):
        fields = None
        exclude = ("reported_user", "reporter_email", "reported_email")


class ReportCreateActionSerializer(BaseReportSerializer):
    class Meta(BaseReportSerializer.Meta):
        read_only_fields = (
            "reported_by", "reported_user", "reporter_email", "reported_email",
            "chat_room", "chat_message", "anon_number",
        )

    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except IntegrityError:
            raise serializers.ValidationError(
                gettext("You already reported this article.")
            )
