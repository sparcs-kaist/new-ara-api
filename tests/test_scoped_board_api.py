import json

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.core.models import Article, ArticleHiddenReason, Board, Scrap
from apps.core.models.board import NameType
from apps.course.models import Course, CourseEnrollment, CourseGroup
from apps.major.models import Major, UserMajor
from apps.user.models import UserProfile
from tests.conftest import TestCase

User = get_user_model()


class TestScopedBoardAPI(TestCase):
    """학과·과목 누적 게시판의 정책을 실제 API 경로에서 검증한다."""

    HOME_MAJOR_ID = 101
    FAVORITE_USER_MAJOR_ID = 202
    OUTSIDER_MAJOR_ID = 303

    def setUp(self):
        super().setUp()

        # 내부 Board helper는 process-local id를 캐시한다. 각 TestCase rollback 뒤
        # 이전 테스트의 PK가 남지 않도록 API 시나리오마다 캐시를 초기화한다.
        from apps.course import board as course_board
        from apps.major import board as major_board

        course_board._cached_board_id = None
        major_board._cached_board_id = None

        self.api_client = APIClient()
        self.major_author = self._create_user("major-author", self.HOME_MAJOR_ID)
        self.major_peer = self._create_user("major-peer", self.HOME_MAJOR_ID)
        self.favorite_user = self._create_user(
            "major-favorite", self.FAVORITE_USER_MAJOR_ID
        )
        self.outsider = self._create_user("major-outsider", self.OUTSIDER_MAJOR_ID)

        self.home_major = Major.objects.create(
            std_dept_id=self.HOME_MAJOR_ID,
            major_code="CS",
            major_name="전산학부",
            major_name_eng="School of Computing",
        )
        UserMajor.objects.create(user=self.favorite_user, major=self.home_major)

        self.course_group = CourseGroup.objects.create(
            course_code="CS101",
            professors_key="1",
            title="프로그래밍기초",
            title_year=2026,
            title_semester=3,
        )
        self.spring_course = self._create_course(2026, 1, 1001)
        self.fall_course = self._create_course(2026, 3, 1002)
        CourseEnrollment.objects.create(
            user=self.major_author,
            course=self.spring_course,
            last_seen_in_otl_at=timezone.now(),
        )
        CourseEnrollment.objects.create(
            user=self.favorite_user,
            course=self.fall_course,
            last_seen_in_otl_at=timezone.now(),
        )

    def _create_user(self, username, std_dept_id):
        user = User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
        )
        UserProfile.objects.create(
            user=user,
            nickname=f"nickname-{username}",
            group=UserProfile.UserGroup.KAIST_MEMBER,
            agree_terms_of_service_at=timezone.now(),
            sso_user_info={
                "first_name": username,
                "last_name": "Test",
                "kaist_info": json.dumps({"ku_kname": username}),
                "kaist_v2_info": json.dumps(
                    {
                        "std_dept_id": std_dept_id,
                        "std_dept_kor_nm": f"학과-{std_dept_id}",
                        "std_dept_eng_nm": f"Department {std_dept_id}",
                    }
                ),
            },
        )
        return user

    def _create_course(self, year, semester, otl_course_id):
        return Course.objects.create(
            course_code=self.course_group.course_code,
            title=self.course_group.title,
            department_name="전산학부",
            year=year,
            semester=semester,
            group=self.course_group,
            professors_key=self.course_group.professors_key,
            credit="3.0",
            otl_course_id=otl_course_id,
            otl_lecture_ids=[otl_course_id],
        )

    def _request(self, user, method, url, data=None):
        self.api_client.force_authenticate(user=user)
        return getattr(self.api_client, method)(url, data=data, format="json")

    @staticmethod
    def _article_payload(name_type, suffix=""):
        return {
            "title": f"scoped article {suffix}",
            "content": f"scoped content {suffix}",
            "content_text": f"scoped content text {suffix}",
            "name_type": name_type.name,
        }

    @staticmethod
    def _comment_payload(article_id, suffix=""):
        return {
            "content": f"scoped comment {suffix}",
            "parent_article": article_id,
            "parent_comment": None,
        }

    @staticmethod
    def _report_payload(article_id, suffix=""):
        return {
            "parent_article": article_id,
            "type": "others",
            "content": f"scoped report {suffix}",
        }

    def _major_articles_url(self, major_id=None):
        return reverse(
            "major:major-article-list",
            kwargs={"std_dept_id": major_id or self.HOME_MAJOR_ID},
        )

    def _major_article_url(self, article_id, major_id=None):
        return reverse(
            "major:major-article-detail",
            kwargs={
                "std_dept_id": major_id or self.HOME_MAJOR_ID,
                "pk": article_id,
            },
        )

    def _course_articles_url(self, course):
        return reverse("course:course-article-list", kwargs={"course_id": course.id})

    def _course_article_url(self, course, article_id):
        return reverse(
            "course:course-article-detail",
            kwargs={"course_id": course.id, "pk": article_id},
        )

    @staticmethod
    def _article_vote_url(article_id):
        return reverse("core:article-vote-positive", kwargs={"pk": article_id})

    @staticmethod
    def _comment_url(comment_id):
        return reverse("core:comment-detail", kwargs={"pk": comment_id})

    @staticmethod
    def _comment_vote_url(comment_id):
        return reverse("core:comment-vote-positive", kwargs={"pk": comment_id})

    def _create_major_article(self, user, name_type=NameType.REGULAR, suffix=""):
        response = self._request(
            user,
            "post",
            self._major_articles_url(),
            self._article_payload(name_type, suffix),
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        return response

    def _create_course_article(
        self, user, course, name_type=NameType.REGULAR, suffix=""
    ):
        response = self._request(
            user,
            "post",
            self._course_articles_url(course),
            self._article_payload(name_type, suffix),
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        return response

    def _scrap(self, user, article_id):
        return self._request(
            user,
            "post",
            reverse("core:scrap-list"),
            {"parent_article": article_id},
        )

    def _report(self, user, article_id, suffix=""):
        return self._request(
            user,
            "post",
            reverse("core:report-list"),
            self._report_payload(article_id, suffix),
        )

    def _scrapped_parent_article(self, user, article_id):
        response = self._request(user, "get", reverse("core:scrap-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        return next(
            item["parent_article"]
            for item in response.data["results"]
            if item["parent_article"]["id"] == article_id
        )

    def _create_comment(self, user, article_id, suffix=""):
        response = self._request(
            user,
            "post",
            reverse("core:comment-list"),
            self._comment_payload(article_id, suffix),
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        return response

    def test_home_major_can_write_comment_and_vote_with_both_name_types(self):
        created_articles = []
        for name_type in (NameType.ANONYMOUS, NameType.REGULAR):
            created = self._create_major_article(
                self.major_author, name_type, name_type.name.lower()
            )
            self.assertEqual(created.data["name_type"], name_type)

            detail = self._request(
                self.major_peer,
                "get",
                self._major_article_url(created.data["id"]),
            )
            self.assertEqual(detail.status_code, status.HTTP_200_OK)
            self.assertEqual(detail.data["name_type"], name_type)
            created_articles.append(created.data["id"])

        target_article_id = created_articles[-1]
        comment = self._create_comment(
            self.major_peer, target_article_id, "same-major"
        )
        self.assertEqual(comment.data["name_type"], NameType.REGULAR)

        article_vote = self._request(
            self.major_peer,
            "post",
            self._article_vote_url(target_article_id),
        )
        comment_vote = self._request(
            self.major_author,
            "post",
            self._comment_vote_url(comment.data["id"]),
        )
        self.assertEqual(article_vote.status_code, status.HTTP_200_OK)
        self.assertEqual(comment_vote.status_code, status.HTTP_200_OK)

    def test_favorite_major_can_read_and_vote_but_cannot_write(self):
        article = self._create_major_article(self.major_author)
        comment = self._create_comment(
            self.major_peer, article.data["id"], "favorite-target"
        )

        article_detail = self._request(
            self.favorite_user,
            "get",
            self._major_article_url(article.data["id"]),
        )
        comment_detail = self._request(
            self.favorite_user, "get", self._comment_url(comment.data["id"])
        )
        self.assertEqual(article_detail.status_code, status.HTTP_200_OK)
        self.assertEqual(comment_detail.status_code, status.HTTP_200_OK)

        article_vote = self._request(
            self.favorite_user,
            "post",
            self._article_vote_url(article.data["id"]),
        )
        comment_vote = self._request(
            self.favorite_user,
            "post",
            self._comment_vote_url(comment.data["id"]),
        )
        self.assertEqual(article_vote.status_code, status.HTTP_200_OK)
        self.assertEqual(comment_vote.status_code, status.HTTP_200_OK)

        detail_after_vote = self._request(
            self.favorite_user,
            "get",
            self._major_article_url(article.data["id"]),
        )
        self.assertIs(detail_after_vote.data["my_vote"], True)
        nested_comment = next(
            item
            for item in detail_after_vote.data["comments"]
            if item["id"] == comment.data["id"]
        )
        self.assertIs(nested_comment["my_vote"], True)

        article_write = self._request(
            self.favorite_user,
            "post",
            self._major_articles_url(),
            self._article_payload(NameType.REGULAR, "favorite-denied"),
        )
        comment_write = self._request(
            self.favorite_user,
            "post",
            reverse("core:comment-list"),
            self._comment_payload(article.data["id"], "favorite-denied"),
        )
        self.assertEqual(article_write.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(comment_write.status_code, status.HTTP_403_FORBIDDEN)

    def test_unrelated_major_cannot_read_write_or_vote(self):
        article = self._create_major_article(self.major_author)
        comment = self._create_comment(
            self.major_peer, article.data["id"], "outsider-target"
        )

        requests = (
            self._request(
                self.outsider,
                "get",
                self._major_article_url(article.data["id"]),
            ),
            self._request(
                self.outsider, "get", self._comment_url(comment.data["id"])
            ),
            self._request(
                self.outsider,
                "post",
                self._major_articles_url(),
                self._article_payload(NameType.REGULAR, "outsider-denied"),
            ),
            self._request(
                self.outsider,
                "post",
                reverse("core:comment-list"),
                self._comment_payload(article.data["id"], "outsider-denied"),
            ),
            self._request(
                self.outsider,
                "post",
                self._article_vote_url(article.data["id"]),
            ),
            self._request(
                self.outsider,
                "post",
                self._comment_vote_url(comment.data["id"]),
            ),
        )
        for response in requests:
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_same_course_group_across_terms_has_full_interaction_access(self):
        created_articles = []
        for name_type in (NameType.ANONYMOUS, NameType.REGULAR):
            created = self._request(
                self.major_author,
                "post",
                self._course_articles_url(self.spring_course),
                self._article_payload(name_type, f"course-{name_type.name.lower()}"),
            )
            self.assertEqual(
                created.status_code, status.HTTP_201_CREATED, created.data
            )
            self.assertEqual(created.data["name_type"], name_type)
            created_articles.append(created.data["id"])

            cross_term_detail = self._request(
                self.favorite_user,
                "get",
                self._course_article_url(self.fall_course, created.data["id"]),
            )
            self.assertEqual(cross_term_detail.status_code, status.HTTP_200_OK)
            self.assertEqual(cross_term_detail.data["name_type"], name_type)

        target_article_id = created_articles[-1]
        comment = self._create_comment(
            self.major_author, target_article_id, "cross-term-target"
        )

        cross_term_article = self._request(
            self.favorite_user,
            "post",
            self._course_articles_url(self.spring_course),
            self._article_payload(NameType.REGULAR, "cross-term-write"),
        )
        cross_term_comment = self._request(
            self.favorite_user,
            "post",
            reverse("core:comment-list"),
            self._comment_payload(target_article_id, "cross-term-write"),
        )
        article_vote = self._request(
            self.favorite_user,
            "post",
            self._article_vote_url(target_article_id),
        )
        comment_vote = self._request(
            self.favorite_user,
            "post",
            self._comment_vote_url(comment.data["id"]),
        )
        self.assertEqual(cross_term_article.status_code, status.HTTP_201_CREATED)
        self.assertEqual(cross_term_comment.status_code, status.HTTP_201_CREATED)
        self.assertEqual(article_vote.status_code, status.HTTP_200_OK)
        self.assertEqual(comment_vote.status_code, status.HTTP_200_OK)

        detail_after_vote = self._request(
            self.favorite_user,
            "get",
            self._course_article_url(self.fall_course, target_article_id),
        )
        self.assertIs(detail_after_vote.data["my_vote"], True)
        nested_comment = next(
            item
            for item in detail_after_vote.data["comments"]
            if item["id"] == comment.data["id"]
        )
        self.assertIs(nested_comment["my_vote"], True)

    def test_scrap_and_report_are_limited_to_home_major_and_enrolled_group(self):
        major_article_id = self._create_major_article(
            self.major_author, suffix="scrap-report"
        ).data["id"]
        course_article_id = self._create_course_article(
            self.major_author, self.spring_course, suffix="scrap-report"
        ).data["id"]

        # 본인 SSO 학과, 같은 CourseGroup 수강.
        for user, article_id in (
            (self.major_peer, major_article_id),
            (self.favorite_user, course_article_id),
        ):
            scrap = self._scrap(user, article_id)
            report = self._report(user, article_id, "allowed")
            self.assertEqual(scrap.status_code, status.HTTP_201_CREATED, scrap.data)
            self.assertEqual(report.status_code, status.HTTP_201_CREATED, report.data)

        # 추가한 타 학과, 미수강.
        for user, article_id in (
            (self.favorite_user, major_article_id),
            (self.outsider, major_article_id),
            (self.major_peer, course_article_id),
            (self.outsider, course_article_id),
        ):
            scrap = self._scrap(user, article_id)
            report = self._report(user, article_id, "denied")
            self.assertEqual(scrap.status_code, status.HTTP_403_FORBIDDEN, scrap.data)
            self.assertEqual(report.status_code, status.HTTP_403_FORBIDDEN, report.data)

        self.assertEqual(
            Scrap.objects.filter(
                parent_article_id__in=(major_article_id, course_article_id)
            ).count(),
            2,
        )

    def test_scrap_list_unmasks_scoped_articles_for_users_with_access(self):
        major_article_id = self._create_major_article(
            self.major_author, suffix="scrap-list-major"
        ).data["id"]
        course_article_id = self._create_course_article(
            self.major_author, self.spring_course, suffix="scrap-list-course"
        ).data["id"]

        for user, article_id in (
            (self.major_peer, major_article_id),
            (self.favorite_user, course_article_id),
        ):
            created = self._scrap(user, article_id)
            self.assertEqual(
                created.status_code, status.HTTP_201_CREATED, created.data
            )

            listed = self._scrapped_parent_article(user, article_id)
            self.assertIsNotNone(listed["title"])
            self.assertIsNotNone(listed["content"])
            self.assertIs(listed["is_hidden"], False)
            self.assertEqual(listed["why_hidden"], [])

    def test_scrap_list_keeps_masking_scoped_articles_without_access(self):
        major_article_id = self._create_major_article(
            self.major_author, suffix="masked-major"
        ).data["id"]
        course_article_id = self._create_course_article(
            self.major_author, self.spring_course, suffix="masked-course"
        ).data["id"]

        # 생성 가드를 우회해 이미 스크랩된 상태를 만든다. 접근권이 없으면
        # 목록에서는 계속 마스킹돼야 한다.
        Scrap.objects.create(
            parent_article_id=major_article_id, scrapped_by=self.favorite_user
        )
        Scrap.objects.create(
            parent_article_id=course_article_id, scrapped_by=self.major_peer
        )

        for user, article_id in (
            (self.favorite_user, major_article_id),
            (self.major_peer, course_article_id),
        ):
            listed = self._scrapped_parent_article(user, article_id)
            self.assertIsNone(listed["title"])
            self.assertIsNone(listed["content"])
            self.assertIs(listed["is_hidden"], True)
            self.assertIn(
                ArticleHiddenReason.ACCESS_DENIED_CONTENT.value, listed["why_hidden"]
            )

    def test_scrap_list_keeps_masking_general_board_article_without_read_access(self):
        private_board = Board.objects.create(
            slug="scoped-private-board",
            ko_name="비공개 게시판",
            en_name="Private Board",
            read_access_mask=0,
        )
        private_article = Article.objects.create(
            title="비공개 글",
            content="비공개 내용",
            content_text="비공개 텍스트",
            name_type=NameType.REGULAR,
            created_by=self.major_author,
            parent_board=private_board,
        )
        Scrap.objects.create(
            parent_article=private_article, scrapped_by=self.major_peer
        )

        listed = self._scrapped_parent_article(self.major_peer, private_article.id)
        self.assertIsNone(listed["title"])
        self.assertIsNone(listed["content"])
        self.assertIs(listed["is_hidden"], True)
        self.assertIn(
            ArticleHiddenReason.ACCESS_DENIED_CONTENT.value, listed["why_hidden"]
        )
