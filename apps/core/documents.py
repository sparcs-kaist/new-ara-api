from django.conf import settings
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from django.apps import apps
from elasticsearch_dsl import analyzer, tokenizer

from apps.core.models import Article
from apps.user.models import UserProfile


# _nori = 'nori'

_nori = analyzer(
    'nori_custom',
    tokenizer = tokenizer(
        'nori_tokenizer',
        # decompound_mode = 'mixed',
        # user_dictionary_rules = [
        #     '카이스트',
        #     '데구 데이타구조',
        # ] 
    ),
    filter = ['nori_number']
)


@registry.register_document
class ArticleDocument(Document):

    title = fields.TextField(attr='title', analyzer=_nori)
    content_text = fields.TextField(attr='content_text', analyzer=_nori)

    created_by = fields.ObjectField(
        properties={
            'id': fields.IntegerField(),
            'profile': fields.NestedField(
                properties = {
                    'nickname': fields.TextField()
                }
            )
        }
    )

    class Index:
        name = 'articles'
        settings = {
            'number_of_shards': 3,
            'number_of_replicas': 1,
        }

    class Django:
        model = Article

        fields = [
            'created_at',
        ]

        related_models = [settings.AUTH_USER_MODEL, UserProfile]

    def get_instances_from_related(self, related_instance):

        # I know this is a terrible hack, but there is no better way to get the auth model class
        if isinstance(related_instance, apps.get_model( *settings.AUTH_USER_MODEL.split('.') )):
            return related_instance.article_set.all()
        elif isinstance(related_instance, UserProfile):
            return related_instance.user.article_set.all()

