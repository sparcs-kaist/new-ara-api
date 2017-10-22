from rest_framework import serializers


from apps.core.models import CommentUpdateLog


class CommentUpdateLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommentUpdateLog
        fields = '__all__'


