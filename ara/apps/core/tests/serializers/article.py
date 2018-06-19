from django.test import TestCase
from django.contrib.auth.models import User

from apps.core.models import Board, Topic
from apps.core.serializers.article import ArticleCreateActionSerializer, ArticleUpdateActionSerializer


class ArticleSerializerLevelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='',
            username='guest',
            password='guest',
        )

        self.board1 = Board.objects.create(
            ko_name='ko name for board#1',
            en_name='en name for board#1',
            ko_description='ko description for board#1',
            en_description='en description for board#1',
        )

        self.topic1 = Topic.objects.create(
            ko_name='ko name for topic#1',
            en_name='en name for topic#1',
            ko_description='ko description for topic#1',
            en_description='en description for topic#1',
            parent_board=self.board1,
        )

        self.board2 = Board.objects.create(
            ko_name='ko name for board#2',
            en_name='en name for board#2',
            ko_description='ko description for board#2',
            en_description='en description for board#2',
        )

        self.topic2 = Topic.objects.create(
            ko_name='ko name for topic#2',
            en_name='en name for topic#2',
            ko_description='ko description for topic#2',
            en_description='en description for topic#2',
            parent_board=self.board2,
        )

    def test_create_article(self):
        serializer = ArticleCreateActionSerializer(data={
            'title': 'title for article',
            'content': 'content for article',
            'is_anonymous': True,
            'is_content_sexual': True,
            'is_content_social': True,
            'parent_topic': self.topic1.id,
            'parent_board': self.board1.id,
        })

        serializer.is_valid(raise_exception=True)

        serializer.save(
            created_by=self.user,
        )

    def test_create_article_with_default(self):
        serializer = ArticleCreateActionSerializer(data={
            'title': 'title for article',
            'content': 'content for article',
            'parent_board': self.board1.id,
        })

        serializer.is_valid(raise_exception=True)

        instance = serializer.save(
            created_by=self.user,
        )

        self.assertEqual(instance.is_anonymous, False)
        self.assertEqual(instance.is_content_sexual, False)
        self.assertEqual(instance.is_content_social, False)

    def test_create_article_with_integrity_error(self):
        serializer = ArticleCreateActionSerializer(data={
            'title': 'title for article',
            'content': 'content for article',
            'is_anonymous': True,
            'is_content_sexual': True,
            'is_content_social': True,
            'parent_topic': self.topic1.id,
            'parent_board': self.board2.id,
        })

        serializer.is_valid(raise_exception=True)

        with self.assertRaises(Exception):
            serializer.save(
                created_by=self.user,
            )

    def test_update_article(self):
        initial_data = {
            'title': 'title for article',
            'content': 'content for article',
            'is_anonymous': True,
            'is_content_sexual': True,
            'is_content_social': True,
            'parent_topic': self.topic1.id,
            'parent_board': self.board1.id,
        }

        updated_data = {
            'title': 'new title for article',
            'content': 'new content for article',
            'is_anonymous': False,
            'is_content_sexual': False,
            'is_content_social': False,
            'parent_topic': self.topic2.id,
            'parent_board': self.board2.id,
        }

        serializer = ArticleCreateActionSerializer(data=initial_data)

        serializer.is_valid(raise_exception=True)

        instance = serializer.save(
            created_by=self.user,
        )

        for field, value in updated_data.items():
            serializer = ArticleUpdateActionSerializer(instance=instance, data={
                field: value
            }, partial=True)

            serializer.is_valid(raise_exception=True)

            serializer.save()

            if field in serializer.get_fields():
                self.assertEqual(getattr(instance, field), updated_data[field])

            else:
                if isinstance(getattr(instance, field), Topic) or isinstance(getattr(instance, field), Board):
                    self.assertEqual(getattr(instance, field).id, initial_data[field])

                else:
                    self.assertEqual(getattr(instance, field), initial_data[field])
