import datetime
import json
from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.core.article_scope import general_article_filter, scoped_article_sql_condition
from apps.core.models import Article, ArticleReadLog, Board
from apps.core.models.board import NameType
from apps.core.serializers.article import (
    ArticleCreateActionSerializer,
    ArticleUpdateActionSerializer,
)
from apps.course.access import is_course_article
from apps.course.board import get_courses_board_id
from apps.course.models import Course, CourseEnrollment, CourseGroup
from apps.major.board import get_major_board_id
from apps.major.models import Major, UserMajor
from apps.user.models import UserProfile
from tests.conftest import TestCase

User = get_user_model()


class ArticleScopeGuardTest(SimpleTestCase):
    def test_general_article_writes_cannot_set_scoped_relations(self):
        for serializer_class in (
            ArticleCreateActionSerializer,
            ArticleUpdateActionSerializer,
        ):
            fields = serializer_class().fields
            self.assertTrue(fields["related_course"].read_only)
            self.assertTrue(fields["related_course_group"].read_only)
            self.assertTrue(fields["related_major"].read_only)

    def test_general_article_filter_uses_course_group_scope(self):
        self.assertEqual(
            general_article_filter(),
            {
                "related_course_group__isnull": True,
                "related_major__isnull": True,
            },
        )
        sql = scoped_article_sql_condition()
        self.assertIn("related_course_group_id", sql)
        self.assertNotIn("`related_course_id`", sql)

    def test_course_article_detection_uses_group_scope(self):
        self.assertTrue(
            is_course_article(
                SimpleNamespace(related_course_id=None, related_course_group_id=10)
            )
        )
        self.assertFalse(
            is_course_article(
                SimpleNamespace(related_course_id=20, related_course_group_id=None)
            )
        )


class GeneralArticleScopeExclusionTest(TestCase):
    """일반 경로가 scoped article을 실제로 빼는지 API로 검증한다.

    요청자는 학과글·과목글 양쪽에 접근 권한이 있는 유저다. 권한 없는 유저로
    검증하면 scope filter가 빠져도 다른 사유로 통과해 회귀를 놓친다.
    """

    STD_DEPT_ID = 404

    def setUp(self):
        super().setUp()

        # 내부 Board helper는 process-local id를 캐시한다. 각 TestCase rollback 뒤
        # 이전 테스트의 PK가 남지 않도록 API 시나리오마다 캐시를 초기화한다.
        from apps.course import board as course_board
        from apps.major import board as major_board

        course_board._cached_board_id = None
        major_board._cached_board_id = None

        self.api_client = APIClient()
        self.user = self._create_user()

        self.board = Board.objects.create(
            slug="scope guard board",
            ko_name="스코프 가드 게시판",
            en_name="Scope Guard Board",
        )
        self.general_article = self._create_article("general-1", self.board.id)
        self.general_article2 = self._create_article("general-2", self.board.id)
        self.target_article = self._create_article("general-target", self.board.id)

        self.major = Major.objects.create(
            std_dept_id=self.STD_DEPT_ID,
            major_code="CS",
            major_name="전산학부",
            major_name_eng="School of Computing",
        )
        UserMajor.objects.create(user=self.user, major=self.major)
        self.major_article = self._create_article(
            "major",
            get_major_board_id(),
            related_major=self.major,
        )

        self.course_group = CourseGroup.objects.create(
            course_code="CS101",
            professors_key="1",
            title="프로그래밍기초",
            title_year=2026,
            title_semester=3,
        )
        self.course = Course.objects.create(
            course_code=self.course_group.course_code,
            title=self.course_group.title,
            department_name="전산학부",
            year=2026,
            semester=3,
            group=self.course_group,
            professors_key=self.course_group.professors_key,
            credit="3.0",
            otl_course_id=2001,
            otl_lecture_ids=[2001],
        )
        CourseEnrollment.objects.create(
            user=self.user,
            course=self.course,
            last_seen_in_otl_at=timezone.now(),
        )
        self.course_article = self._create_article(
            "course",
            get_courses_board_id(),
            related_course=self.course,
            related_course_group=self.course_group,
        )

    def _create_user(self):
        user = User.objects.create_user(
            username="scope-guard",
            email="scope-guard@example.com",
        )
        UserProfile.objects.create(
            user=user,
            nickname="nickname-scope-guard",
            group=UserProfile.UserGroup.KAIST_MEMBER,
            agree_terms_of_service_at=timezone.now(),
            sso_user_info={
                "first_name": "scope-guard",
                "last_name": "Test",
                "kaist_info": json.dumps({"ku_kname": "scope-guard"}),
                "kaist_v2_info": json.dumps(
                    {
                        "std_dept_id": self.STD_DEPT_ID,
                        "std_dept_kor_nm": "전산학부",
                        "std_dept_eng_nm": "School of Computing",
                    }
                ),
            },
        )
        return user

    def _create_article(self, suffix, board_id, **scope_kwargs):
        return Article.objects.create(
            title=f"scope guard article {suffix}",
            content=f"scope guard content {suffix}",
            content_text=f"scope guard content text {suffix}",
            name_type=NameType.REGULAR,
            created_by=self.user,
            parent_board_id=board_id,
            **scope_kwargs,
        )

    def _read(self, article, minutes_ago):
        return ArticleReadLog.objects.create(
            read_by=self.user,
            article=article,
            created_at=timezone.now() - datetime.timedelta(minutes=minutes_ago),
        )

    def _get(self, url, data=None):
        self.api_client.force_authenticate(user=self.user)
        return self.api_client.get(url, data=data, format="json")

    def _result_ids(self, response):
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        return [item["id"] for item in response.data["results"]]

    def test_article_list_excludes_scoped_articles(self):
        ids = self._result_ids(self._get(reverse("core:article-list")))

        self.assertIn(self.general_article.id, ids)
        self.assertIn(self.general_article2.id, ids)
        self.assertNotIn(self.major_article.id, ids)
        self.assertNotIn(self.course_article.id, ids)

    def test_article_top_excludes_scoped_articles(self):
        ids = self._result_ids(self._get(reverse("core:article-top")))

        self.assertIn(self.general_article.id, ids)
        self.assertIn(self.general_article2.id, ids)
        self.assertNotIn(self.major_article.id, ids)
        self.assertNotIn(self.course_article.id, ids)

    def test_article_recent_returns_general_articles_and_excludes_scoped(self):
        self._read(self.general_article, 30)
        self._read(self.major_article, 20)
        self._read(self.general_article2, 10)
        self._read(self.course_article, 5)

        response = self._get(reverse("core:article-recent"))

        self.assertEqual(
            self._result_ids(response),
            [self.general_article2.id, self.general_article.id],
        )
        self.assertEqual(response.data["num_items"], 2)

    def test_recent_side_articles_exclude_scoped_articles(self):
        # scoped article이 target 바로 앞·뒤에 오도록 읽어, scope filter가 빠지면
        # side article로 튀어나오는 배치를 만든다.
        self._read(self.general_article, 50)
        self._read(self.major_article, 40)
        self._read(self.target_article, 30)
        self._read(self.course_article, 20)
        self._read(self.general_article2, 10)

        response = self._get(
            reverse("core:article-detail", kwargs={"pk": self.target_article.id}),
            {"from_view": "recent"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        side_articles = response.data["side_articles"]
        self.assertEqual(side_articles["before"]["id"], self.general_article.id)
        self.assertEqual(side_articles["after"]["id"], self.general_article2.id)
