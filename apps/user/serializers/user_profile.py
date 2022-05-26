import typing
from django.utils.translation import gettext
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from rest_framework import serializers

from ara.classes.serializers import MetaDataModelSerializer
from apps.user.models import UserProfile


class BaseUserProfileSerializer(MetaDataModelSerializer):
    email = serializers.SerializerMethodField()
    is_school_admin = serializers.SerializerMethodField()
    is_official = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = '__all__'

    @staticmethod
    def get_email(obj) -> typing.Optional[str]:
        if obj.email.endswith('@sso.sparcs.org'):
            return None
        return obj.email

    @staticmethod
    def get_is_school_admin(obj) -> bool:
        return obj.is_school_admin

    @staticmethod
    def get_is_official(obj) -> bool:
        return obj.is_official


class UserProfileSerializer(BaseUserProfileSerializer):
    extra_preferences = serializers.JSONField(
        read_only=True,
    )


class UserProfileUpdateActionSerializer(BaseUserProfileSerializer):
    class Meta(BaseUserProfileSerializer.Meta):
        read_only_fields = (
            'sid',
            'user',
        )

    def validate_nickname(self, value) -> str:
        nickname_changed = self.instance and value != self.instance.nickname
        if nickname_changed and not self.instance.can_change_nickname():
            next_change_date = self.instance.nickname_updated_at + relativedelta(months=3)
            raise serializers.ValidationError(
                gettext('Nicknames can only be changed every 3 months. (can\'t change until %(date)s)')
                % {'date': next_change_date.strftime("%Y/%m/%d")}
            )
        return value

    def update(self, instance, validated_data):
        new_nickname = validated_data.get('nickname')
        old_nickname = instance.nickname if instance else None
        if instance and new_nickname and old_nickname != new_nickname:
            validated_data['nickname_updated_at'] = timezone.now()
        return super(BaseUserProfileSerializer, self).update(instance, validated_data)

    extra_preferences = serializers.JSONField()


class PublicUserProfileSerializer(BaseUserProfileSerializer):
    class Meta(BaseUserProfileSerializer.Meta):
        fields = (
            'picture',
            'nickname',
            'user',
            'is_official',
            'is_school_admin',
        )


class MyPageUserProfileSerializer(BaseUserProfileSerializer):
    num_articles = serializers.SerializerMethodField()
    num_comments = serializers.SerializerMethodField()
    num_positive_votes = serializers.SerializerMethodField()

    @staticmethod
    def get_num_articles(obj):
        from apps.core.models import Article
        num_articles = Article.objects.filter(created_by=obj.user).count()
        return num_articles

    @staticmethod
    def get_num_comments(obj):
        from apps.core.models import Comment
        num_comments = Comment.objects.filter(created_by=obj.user).count()
        return num_comments

    @staticmethod
    def get_num_positive_votes(obj):
        from apps.core.models import Vote
        num_article_votes = Vote.objects.filter(parent_article__created_by=obj.user, is_positive=True).count()
        num_comment_votes = Vote.objects.filter(parent_comment__created_by=obj.user, is_positive=True).count()
        return num_article_votes + num_comment_votes
