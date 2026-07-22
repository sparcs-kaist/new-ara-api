"""학과 게시판 목록용 serializer."""

from rest_framework import serializers

from apps.major.models import Major


class MajorSerializer(serializers.ModelSerializer):
    """전체 학과 게시판 목록 응답.

    is_added: 현재 요청 유저가 이 학과를 add 해 뒀는지 (토글 UI 용).
    N+1 방지를 위해 view 가 context["added_major_ids"] (set) 를 주입한다.

    readers_count: 이 학과 게시판을 add 한 유저 수. view 의 queryset 이
    annotate 해 주며, annotate 되지 않은 객체가 들어와도 동작하도록 fallback.
    """

    is_added = serializers.SerializerMethodField(read_only=True)
    readers_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Major
        fields = (
            "std_dept_id",
            "major_code",
            "major_name",
            "major_name_eng",
            "is_added",
            "readers_count",
        )
        read_only_fields = fields

    def get_is_added(self, obj) -> bool:
        added_ids = self.context.get("added_major_ids") or set()
        return obj.std_dept_id in added_ids

    def get_readers_count(self, obj) -> int:
        count = getattr(obj, "readers_count", None)
        if count is None:
            return obj.user_additions.count()
        return count
