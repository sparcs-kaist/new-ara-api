from rest_framework import serializers
from apps.kaist.models import Post

class TrendingPostsSerializer(serializers.ModelSerializer):
    growth = serializers.IntegerField(source='view_count_growth', read_only=True)
    current_view_count = serializers.IntegerField(source='view_count', read_only=True)
    portal_url = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = (
            'id',
            'title',
            'writer_name',
            'current_view_count',
            'growth',
            'registered_at',
            'portal_url',
        )

    def get_portal_url(self, obj):
        return f"https://portal.kaist.ac.kr/kaist/portal/board/ntc/0#{obj.id}"