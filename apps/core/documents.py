from django.conf import settings
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from django.apps import apps
from elasticsearch_dsl import analyzer, tokenizer
from elasticsearch_dsl.analysis import token_filter

from apps.core.models import Article
from apps.user.models import UserProfile


custom_analyzer = analyzer(
    'nori_user_dict',
    type='custom',
    tokenizer=tokenizer(
        'nori_user_dict_tkn',
        type='nori_tokenizer',
        decompound_mode='mixed',
        user_dictionary='analysis/userdict_ko.txt'
    ),
    filter=[
        'nori_readingform',
        token_filter(
            'synonym',
            type='synonym',
            expand=True,
            synonyms_path='analysis/synonym.txt'
        ),
        *[
            token_filter(
                f'extend_{x}_to_4',
                type='pattern_replace',
                pattern='(^.{%d}$)'%x,
                replacement=('$1'+' '*(4-x)),
                all=False
            ) for x in range(1,4)
        ],
        token_filter(
            '4_5_grams',
            type='ngram',
            min_gram=4,
            max_gram=5
        ),
        'lowercase',
    ]
)


@registry.register_document
class ArticleDocument(Document):

    title = fields.TextField(attr='title', analyzer=custom_analyzer)
    content_text = fields.TextField(attr='content_text', analyzer=custom_analyzer)
    created_by_nickname = fields.KeywordField(attr='created_by_nickname')

    class Index:
        name = 'articles'
        settings = {
            'number_of_shards': 3,
            'number_of_replicas': 1,
            # 'max_ngram_diff': 50,
        }

    class Django:
        model = Article

        fields = [
            'created_at',
        ]

        related_models = [settings.AUTH_USER_MODEL, UserProfile]

    def get_queryset(self):
        return super(ArticleDocument, self).get_queryset().prefetch_related('created_by').prefetch_related('created_by__profile')

    @staticmethod
    def get_id_set(field_name, search_value):
        return [
            x.meta.id
            for x
            in ArticleDocument.search().filter('match', **{field_name: search_value})[0:200].execute()
        ]

    @staticmethod
    def get_instances_from_related(related_instance):
        if isinstance(related_instance, apps.get_model(settings.AUTH_USER_MODEL)):
            return related_instance.article_set.all()
        elif isinstance(related_instance, UserProfile):
            return related_instance.user.article_set.all()

