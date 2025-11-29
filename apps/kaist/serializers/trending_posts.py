from rest_framework import serializers
from apps.kaist.models import Post

class TrendingPostsSerializer(serializers.ModelSerializer):
    portal_url = serializers.SerializerMethodField()
    class Meta:
        model = Post
        fields = (
            'id',
            'board_id', #포탈 내에서 작성된 게시판
            'board_name', #포탈 내에서 작성된 게시글
            'title',
            'content',
            'writer_name',
            'writer_department',
            'registered_at',
            'ara_article',
            'portal_url', #포탈의 게시물 링크 (현재 작동 안함. ntc 대신 각각의 게시물에 맞는 항목을 수동으로 매핑해줘야함)
        )

    def get_portal_url(self, obj):
        return f"https://portal.kaist.ac.kr/kaist/portal/board/ntc/0#{obj.id}"