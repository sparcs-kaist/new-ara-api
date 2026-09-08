from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from apps.core.models.board import NameType
from apps.course.serializers.article import (
    CourseArticleCreateSerializer,
    CourseArticleListSerializer,
    CourseArticleSerializer,
)
from apps.major.serializers.article import (
    MajorArticleCreateSerializer,
    MajorArticleListSerializer,
    MajorArticleSerializer,
)


class ScopedArticleNameTypeSerializerTest(SimpleTestCase):
    payload = {
        "title": "title",
        "content": "content",
        "content_text": "content",
    }

    def assert_name_type(self, serializer_class, name_type):
        serializer = serializer_class(
            data={**self.payload, "name_type": name_type},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["name_type"], name_type)

    def test_course_article_accepts_anonymous_and_regular(self):
        self.assert_name_type(
            CourseArticleCreateSerializer,
            NameType.ANONYMOUS.name,
        )
        self.assert_name_type(
            CourseArticleCreateSerializer,
            NameType.REGULAR.name,
        )

    def test_major_article_accepts_anonymous_and_regular(self):
        self.assert_name_type(
            MajorArticleCreateSerializer,
            NameType.ANONYMOUS.name,
        )
        self.assert_name_type(
            MajorArticleCreateSerializer,
            NameType.REGULAR.name,
        )

    def test_existing_defaults_are_preserved(self):
        course = CourseArticleCreateSerializer(data=self.payload)
        major = MajorArticleCreateSerializer(data=self.payload)

        self.assertTrue(course.is_valid(), course.errors)
        self.assertTrue(major.is_valid(), major.errors)
        self.assertEqual(
            course.validated_data["name_type"],
            NameType.ANONYMOUS.name,
        )
        self.assertEqual(
            major.validated_data["name_type"],
            NameType.REGULAR.name,
        )

    def test_realname_is_rejected(self):
        for serializer_class in (
            CourseArticleCreateSerializer,
            MajorArticleCreateSerializer,
        ):
            serializer = serializer_class(
                data={**self.payload, "name_type": NameType.REALNAME.name},
            )
            self.assertFalse(serializer.is_valid())
            self.assertIn("name_type", serializer.errors)

    def test_course_article_persists_selected_name_type(self):
        for name_type in (NameType.ANONYMOUS, NameType.REGULAR):
            serializer = CourseArticleCreateSerializer(
                data={**self.payload, "name_type": name_type.name},
                context={
                    "course": object(),
                    "course_group": object(),
                    "board_id": 1,
                    "request": SimpleNamespace(user=object()),
                },
            )
            self.assertTrue(serializer.is_valid(), serializer.errors)

            with patch(
                "apps.course.serializers.article.Article.objects.create",
                return_value=object(),
            ) as create:
                serializer.save()

            self.assertEqual(create.call_args.kwargs["name_type"], name_type.value)

    def test_major_article_persists_selected_name_type(self):
        for name_type in (NameType.ANONYMOUS, NameType.REGULAR):
            serializer = MajorArticleCreateSerializer(
                data={**self.payload, "name_type": name_type.name},
                context={
                    "major": object(),
                    "board_id": 1,
                    "request": SimpleNamespace(user=object()),
                },
            )
            self.assertTrue(serializer.is_valid(), serializer.errors)

            with patch(
                "apps.major.serializers.article.Article.objects.create",
                return_value=object(),
            ) as create:
                serializer.save()

            self.assertEqual(create.call_args.kwargs["name_type"], name_type.value)

    def test_read_serializers_expose_name_type_and_created_by(self):
        for serializer_class in (
            CourseArticleListSerializer,
            CourseArticleSerializer,
            MajorArticleListSerializer,
            MajorArticleSerializer,
        ):
            fields = serializer_class().fields
            self.assertIn("name_type", fields)
            self.assertIn("created_by", fields)
