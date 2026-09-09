from types import SimpleNamespace

from django.test import SimpleTestCase

from apps.core.article_scope import general_article_filter, scoped_article_sql_condition
from apps.core.serializers.article import (
    ArticleCreateActionSerializer,
    ArticleUpdateActionSerializer,
)
from apps.course.access import is_course_article


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
