"""과목/학과 게시판(scoped board) 용 hidden 판정 보정 믹스인.

과목·학과 게시판 글은 `parent_board` 로 dummy board 를 가진다. 이 board 는
일반 board 라우트로 새어나가지 않게 `read_access_mask=0` 으로 만들어져 있고,
실제 접근 통제는 board mask 가 아니라 IsEnrolledInCourseGroup / IsSameMajor
권한이 담당한다.

그런데 `Article.hidden_reasons` 는 parent_board 의 read mask 를 확인해서
권한이 없으면 ACCESS_DENIED_CONTENT 를 붙인다. 그래서 core 의 Article
serializer 를 그대로 상속하면 scoped 글은 **전원에게** 마스킹돼 버린다.

이 믹스인은 그 사유 하나만 제거한다. 신고 누적(REPORTED)·차단 유저(BLOCKED)·
성인(ADULT)·정치(SOCIAL) 마스킹은 core 와 동일하게 유지된다. serializer 까지
왔다는 것은 view 의 권한 검사를 이미 통과했다는 뜻이므로 안전하다.
"""

from __future__ import annotations

from apps.core.models import ArticleHiddenReason


class ScopedBoardHiddenInfoMixin:
    """`hidden_info` 에서 ACCESS_DENIED_CONTENT 사유만 걷어낸다."""

    def hidden_info(self, obj) -> tuple[bool, bool, list]:
        _, _, reasons = super().hidden_info(obj)
        reasons = [
            reason
            for reason in reasons
            if reason != ArticleHiddenReason.ACCESS_DENIED_CONTENT
        ]
        cannot_override_reasons = [
            reason for reason in reasons if reason not in self.CAN_OVERRIDE_REASONS
        ]
        return len(reasons) > 0, len(cannot_override_reasons) == 0, reasons
