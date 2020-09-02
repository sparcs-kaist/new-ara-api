from django.conf import settings
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry

from apps.core.models import Article
from apps.user.models import UserProfile


@registry.register_document
class ArticleDocument(Document):
    created_by_nickname = fields.TextField(attr='created_by_nickname')

    class Index:
        name = 'articles'
        settings = {
            'number_of_shards': 3,
            'number_of_replicas': 1,
        }

    class Django:
        model = Article

        fields = [
            'title',
            'content_text',
            'created_at',
        ]

        related_models = [settings.AUTH_USER_MODEL, UserProfile]

    def get_queryset(self):
        return super(ArticleDocument, self).get_queryset().prefetch_related('created_by__profile')
