import json

import pytest
from django.test import override_settings
from django.utils import timezone

from apps.core.models import Article
from apps.course import board as course_board
from apps.course.models import Course, CourseEnrollment, CourseGroup
from apps.major import board as major_board
from tests.conftest import RequestSetting, TestCase
from tests.test_meal_photo import MEMORY_STORAGE


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
        # board id 는 프로세스 메모리에 캐시되는데, 테스트마다 DB 가 롤백된다
        course_board._cached_board_id = None
        board_id = course_board.get_courses_board_id()
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

    def test_detail_has_my_scrap(self):
        from apps.core.models import Scrap

        article = Article.objects.get(title="잡담")
        path = f"courses/{self.course.id}/articles/{article.id}"
        assert self.http_request(self.user, "get", path).data["my_scrap"] is None
        scrap = Scrap.objects.create(parent_article=article, scrapped_by=self.user)
        assert self.http_request(self.user, "get", path).data["my_scrap"]["id"] == scrap.id

    @override_settings(STORAGES=MEMORY_STORAGE)
    def test_attachments(self):
        from apps.core.models import Attachment

        image = Attachment.objects.create(file="a.png", alias="a.png", size=1, mimetype="image/png")
        pdf = Attachment.objects.create(file="b.pdf", alias="b.pdf", size=1, mimetype="application/pdf")
        path = f"courses/{self.course.id}/articles"
        res = self.http_request(self.user, "post", path, {"title": "첨부", "content": "본문", "attachments": [image.id]})
        assert res.status_code == 201, res.data
        assert [a["id"] for a in res.data["attachments"]] == [image.id]

        article_id = res.data["id"]
        res = self.http_request(self.user, "patch", f"{path}/{article_id}", {"attachments": [image.id, pdf.id]})
        assert res.status_code == 200, res.data
        detail = self.http_request(self.user, "get", f"{path}/{article_id}").data
        assert sorted(a["id"] for a in detail["attachments"]) == sorted([image.id, pdf.id])
        types = {a["title"]: a["attachment_type"] for a in self.http_request(self.user, "get", path).data["results"]}
        assert types["첨부"] == "BOTH" and types["잡담"] == "NONE"

        # 필드를 빼면 그대로, 빈 목록이면 전부 지운다
        self.http_request(self.user, "patch", f"{path}/{article_id}", {"title": "첨부 수정"})
        assert Article.objects.get(pk=article_id).attachments.count() == 2
        self.http_request(self.user, "patch", f"{path}/{article_id}", {"attachments": []})
        assert Article.objects.get(pk=article_id).attachments.count() == 0


@pytest.mark.usefixtures("set_user_client")
class TestMajorArticleAttachments(TestCase, RequestSetting):
    def setUp(self):
        major_board._cached_board_id = None
        self.user.profile.sso_user_info = {"kaist_v2_info": json.dumps({"std_dept_id": 1234, "std_dept_kor_nm": "전산학부"})}
        self.user.profile.save()

    @override_settings(STORAGES=MEMORY_STORAGE)
    def test_attachments(self):
        from apps.core.models import Attachment

        image = Attachment.objects.create(file="a.png", alias="a.png", size=1, mimetype="image/png")
        path = "majors/1234/articles"
        res = self.http_request(self.user, "post", path, {"title": "첨부", "content": "본문", "attachments": [image.id]})
        assert res.status_code == 201, res.data
        article = Article.objects.get(pk=res.data["id"])
        assert list(article.attachments.values_list("id", flat=True)) == [image.id]
        assert self.http_request(self.user, "get", path).data["results"][0]["attachment_type"] == "IMAGE"
        # 첨부 없이 쓴 글
        res = self.http_request(self.user, "post", path, {"title": "그냥", "content": "본문"})
        assert res.status_code == 201 and res.data["attachments"] == []

        # 필드를 빼면 그대로, 빈 목록이면 전부 지운다
        self.http_request(self.user, "patch", f"{path}/{article.id}", {"title": "첨부 수정"})
        assert article.attachments.count() == 1
        self.http_request(self.user, "patch", f"{path}/{article.id}", {"attachments": []})
        assert article.attachments.count() == 0
