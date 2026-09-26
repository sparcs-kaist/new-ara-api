import pytest
from django.utils import timezone

from apps.core.models import Article
from apps.course.board import get_courses_board_id
from apps.course.models import Course, CourseEnrollment, CourseGroup
from tests.conftest import RequestSetting, TestCase


@pytest.mark.usefixtures("set_user_client")
class TestCourseArticleSearch(TestCase, RequestSetting):
    def setUp(self):
        group = CourseGroup.objects.create(
            course_code="MAS101", professors_key="10", title="미적분학 I", title_year=2026, title_semester=1,
        )
        self.course = Course.objects.create(
            course_code="MAS101", title="미적분학 I", year=2026, semester=1, group=group,
            professors_key="10", otl_course_id=1, otl_lecture_ids=[101],
        )
        CourseEnrollment.objects.create(user=self.user, course=self.course, last_seen_in_otl_at=timezone.now())
        board_id = get_courses_board_id()
        for title, content in [("중간고사 범위", "3장까지"), ("과제 질문", "중간고사 전에 내나요"), ("잡담", "점심")]:
            Article.objects.create(
                title=title, content=content, content_text=content, created_by=self.user,
                parent_board_id=board_id, related_course=self.course, related_course_group=group,
            )

    def test_search_title_and_body(self):
        path = f"courses/{self.course.id}/articles"
        res = self.http_request(self.user, "get", path, querystring="main_search__contains=중간고사")
        assert res.status_code == 200, res.data
        assert sorted(a["title"] for a in res.data["results"]) == ["과제 질문", "중간고사 범위"]
        assert len(self.http_request(self.user, "get", path).data["results"]) == 3
