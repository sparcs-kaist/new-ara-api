"""학과 게시판 목록용 serializer."""

from rest_framework import serializers

from apps.major.models import Major


class MajorSerializer(serializers.ModelSerializer):
    """전체 학과 게시판 목록 응답.

    is_added: 현재 요청 유저의 UserMajor 에 이 학과가 있는지 (홈 학과 포함 → true).
    N+1 방지를 위해 view 가 context["added_major_ids"] (set) 를 주입한다.

    is_mine: 이 학과가 내 SSO(홈) 학과인지. is_added 만으로는 홈 학과와 내가
    추가한 타 학과를 구분할 수 없어(둘 다 true), 이 플래그로 구분한다. 프론트는
    remove 버튼을 is_mine==false 일 때만 노출하면 된다. view 가
    context["my_std_dept_id"] 를 주입한다.

    readers_count: 이 학과 게시판을 읽는 전체 유저 수(홈 학과 학생 + 추가한 유저).
    view 의 queryset 이 annotate 해 주며, annotate 되지 않은 객체가 들어와도
    동작하도록 fallback.
    """

    is_added = serializers.SerializerMethodField(read_only=True)
    is_mine = serializers.SerializerMethodField(read_only=True)
    readers_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Major
        fields = (
            "std_dept_id",
            "major_code",
            "major_name",
            "major_name_eng",
            "is_added",
            "is_mine",
            "readers_count",
        )
        read_only_fields = fields

    def get_is_added(self, obj) -> bool:
        added_ids = self.context.get("added_major_ids") or set()
        return obj.std_dept_id in added_ids

    def get_is_mine(self, obj) -> bool:
        return obj.std_dept_id == self.context.get("my_std_dept_id")

    def get_readers_count(self, obj) -> int:
        count = getattr(obj, "readers_count", None)
        if count is None:
            return obj.user_additions.count()
        return count
