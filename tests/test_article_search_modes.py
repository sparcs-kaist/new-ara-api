import json
from io import StringIO
from urllib.parse import urlencode

import pytest
from django.core.management import call_command
from django.test import SimpleTestCase
from django.utils import timezone

from apps.core.documents import ArticleDocument
from apps.core.models import Article, ArticleReadLog, Board
from apps.core.models.board import NameType
from apps.course import board as course_board
from apps.course.models import Course, CourseEnrollment, CourseGroup
from apps.major import board as major_board
from apps.major.models import Major
from tests.conftest import RequestSetting, TestCase, Utils


class ArticleContentTextTest(SimpleTestCase):
    def test_json_editor_formats(self):
        nodes = [
            {"type": "paragraph", "content": [{"type": "text", "text": "본문"}]},
            {"type": "codeBlock", "content": [{"type": "text", "text": "code"}]},
        ]
        for document in [
            {"type": "doc", "content": nodes},
            {"content": {"type": "doc", "content": nodes}},
        ]:
            assert Article().extract_text_from_json(json.dumps(document)) == "본문\ncode"

    def test_empty_or_malformed_editor_nodes(self):
        for content in [
            "{invalid",
            "{}",
            json.dumps(
                {
                    "content": [
                        None,
                        "invalid",
                        {
                            "type": "paragraph",
                            "content": [False, {"type": "text", "text": 123}],
                        },
                        {"type": "codeBlock", "content": []},
                    ]
                }
            ),
        ]:
            assert Article().extract_text_from_json(content) == ""


@pytest.fixture(scope="class")
def search_mode_index():
    call_command("search_index", "--delete", "-f")
    call_command("search_index", "--create")


@pytest.mark.usefixtures("set_user_client", "search_mode_index")
class TestArticleSearchModes(TestCase, RequestSetting):
    def setUp(self):
        course_board._cached_board_id = None
        major_board._cached_board_id = None
        self.user.profile.sso_user_info = {
            "kaist_v2_info": json.dumps({"std_dept_id": 1234})
        }
        self.user.profile.save()
        author = Utils.create_user(username="search-author", nickname="키워드작성자")
        username_author = Utils.create_user(username="키워드계정", nickname="다른닉네임")
        board = Board.objects.create(ko_name="검색 게시판", en_name="Search board")
        group = CourseGroup.objects.create(
            course_code="CS101",
            professors_key="1",
            title="검색 과목",
            title_year=2026,
            title_semester=1,
        )
        course = Course.objects.create(
            course_code="CS101",
            title="검색 과목",
            year=2026,
            semester=1,
            group=group,
            professors_key="1",
            otl_course_id=1,
        )
        CourseEnrollment.objects.create(
            user=self.user, course=course, last_seen_in_otl_at=timezone.now()
        )
        major = Major.objects.create(std_dept_id=1234, major_name="검색 학과")
        scopes = [
            ("articles", {"parent_board": board}),
            (
                f"courses/{course.id}/articles",
                {
                    "parent_board_id": course_board.get_courses_board_id(),
                    "related_course": course,
                    "related_course_group": group,
                },
            ),
            (
                "majors/1234/articles",
                {
                    "parent_board_id": major_board.get_major_board_id(),
                    "related_major": major,
                },
            ),
        ]
        self.expected = {}
        for path, scope in scopes:
            articles = {}
            for key, title, content, user, name_type in [
                ("title", "키워드 제목", "평문", self.user, NameType.REGULAR),
                ("content", "본문 검색", "<p>키워드</p>", self.user, NameType.REGULAR),
                ("both", "키워드 양쪽", "키워드", self.user, NameType.REGULAR),
                (
                    "json",
                    "에디터 글",
                    json.dumps(
                        {
                            "type": "doc",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [{"type": "text", "text": "키워드 에디터 본문"}],
                                }
                            ],
                        }
                    ),
                    self.user,
                    NameType.REGULAR,
                ),
                ("author", "작성자 검색", "평문", author, NameType.REGULAR),
                ("anonymous", "익명 글", "평문", author, NameType.ANONYMOUS),
                ("realname", "실명 글", "평문", author, NameType.REALNAME),
                ("username", "계정명 글", "평문", username_author, NameType.REGULAR),
            ]:
                articles[key] = Article.objects.create(
                    title=title,
                    content=content,
                    created_by=user,
                    name_type=name_type,
                    **scope,
                ).id
            deleted = Article.objects.create(
                title="키워드 삭제", content="키워드", created_by=author, **scope
            )
            deleted.delete()
            self.expected[path] = articles
            for article_id in articles.values():
                ArticleReadLog.objects.create(read_by=self.user, article_id=article_id)

        # Autosync 설정과 관계없이 실제 ES 색인/검색을 검증한다.
        ArticleDocument().update(ArticleDocument().get_queryset(), refresh=True)
        self.expected["articles/top"] = self.expected["articles"]
        self.expected["articles/recent"] = self.expected["articles"]

    def search(self, path, **params):
        return self.http_request(self.user, "get", path, querystring=urlencode(params))

    def test_each_mode_searches_only_selected_fields(self):
        for path, articles in self.expected.items():
            for mode, keys in [
                ("title", ["title", "both"]),
                ("content", ["content", "both", "json"]),
                ("title_content", ["title", "content", "both", "json"]),
                ("author", ["author"]),
            ]:
                with self.subTest(path=path, mode=mode):
                    res = self.search(
                        path, main_search__contains="키워드", search_type=mode
                    )
                    assert res.status_code == 200, res.data
                    assert res.data["num_items"] == len(keys)
                    assert {a["id"] for a in res.data["results"]} == {
                        articles[k] for k in keys
                    }

    def test_omitting_mode_preserves_existing_search(self):
        for path, articles in self.expected.items():
            keys = ["title", "content", "both", "json"]
            if path.startswith("articles"):
                keys += ["author", "anonymous", "realname"]
            res = self.search(path, main_search__contains="키워드")
            assert res.status_code == 200, res.data
            assert {a["id"] for a in res.data["results"]} == {articles[k] for k in keys}

    def test_invalid_mode_returns_400_even_without_keyword(self):
        for path in self.expected:
            for params in [{}, {"main_search__contains": "키워드"}]:
                res = self.search(path, search_type="invalid", **params)
                assert res.status_code == 400, res.data
                assert "search_type" in res.data

    def test_blank_keyword_does_not_filter(self):
        for path, articles in self.expected.items():
            for params in [{}, {"main_search__contains": "   "}]:
                res = self.search(path, search_type="author", **params)
                assert res.status_code == 200, res.data
                assert {a["id"] for a in res.data["results"]} == set(articles.values())

    def test_author_search_uses_public_nickname(self):
        for path in self.expected:
            for keyword in ["키워드계정", "search-author", "익명"]:
                res = self.search(
                    path, main_search__contains=keyword, search_type="author"
                )
                assert res.status_code == 200, res.data
                assert res.data["num_items"] == 0

    def test_pagination_counts_only_matching_articles(self):
        for path, articles in self.expected.items():
            ids = set()
            for page in (1, 2, 3, 4):
                res = self.search(
                    path,
                    main_search__contains="키워드",
                    search_type="title_content",
                    page_size=1,
                    page=page,
                )
                assert res.status_code == 200, res.data
                assert res.data["num_items"] == 4
                assert res.data["num_pages"] == 4
                ids.update(a["id"] for a in res.data["results"])
            assert ids == {articles[k] for k in ["title", "content", "both", "json"]}

    def test_backfill_restores_existing_json_articles_in_batches(self):
        ids = {articles["json"] for articles in self.expected.values()}
        Article.objects.filter(id__in=ids).update(content_text="")
        for _ in range(2):
            call_command(
                "backfill_article_content_text", batch_size=1, stdout=StringIO()
            )
            assert set(
                Article.objects.filter(id__in=ids).values_list(
                    "content_text", flat=True
                )
            ) == {"키워드 에디터 본문"}

    def test_scoped_search_still_requires_access(self):
        CourseEnrollment.objects.filter(user=self.user).delete()
        self.user.profile.sso_user_info = {}
        self.user.profile.save()
        for path in self.expected:
            if path.startswith("articles"):
                continue
            res = self.search(path, main_search__contains="키워드", search_type="author")
            assert res.status_code == 403, res.data

    def test_search_combines_with_board_filter(self):
        res = self.search(
            "articles",
            main_search__contains="키워드",
            search_type="author",
            board="missing-board",
        )
        assert res.status_code == 200, res.data
        assert res.data["num_items"] == 0

    def test_updated_json_body_is_searchable(self):
        article = Article.objects.get(id=self.expected["articles"]["json"])
        article.content = json.dumps(
            {
                "type": "doc",
                "content": [
                    {"type": "paragraph", "content": [{"type": "text", "text": "수정본문"}]}
                ],
            }
        )
        article.save()
        article.refresh_from_db()
        assert article.content_text == "수정본문"
        ArticleDocument().update(article, refresh=True)
        res = self.search(
            "articles", main_search__contains="수정본문", search_type="content"
        )
        assert res.status_code == 200, res.data
        assert [a["id"] for a in res.data["results"]] == [article.id]
