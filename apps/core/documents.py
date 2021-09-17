from django.conf import settings
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from django.apps import apps
from elasticsearch_dsl import analyzer, tokenizer, Q
from elasticsearch_dsl.query import Query
from elasticsearch_dsl.analysis import token_filter

from apps.core.models import Article
from apps.user.models import UserProfile


ngram_analyzer = analyzer(
    'ngram_anl',
    type='custom',
    tokenizer=tokenizer(
        'ngram_tkn',
        type='char_group',
        tokenize_on_chars=['\n']
    ),
    filter=[
        token_filter(
            'ngram_tkf',
            type='ngram',
            min_gram=1,
            max_gram=10,
        ),
        'lowercase'
    ]
)


newline_analyzer = analyzer(
    'nl_anl',
    type='custom',
    tokenizer=tokenizer(
        'nl_tkn',
        type='char_group',
        tokenize_on_chars=['\n']
    ),
    filter=[
        token_filter(
            'nl_syn_tkf',
            type='synonym',
            expand=True,
            synonyms_path='analysis/synonym.txt'
        ),
        'lowercase'
    ]
)


@registry.register_document
class ArticleDocument(Document):

    title = fields.TextField(attr='title', analyzer=ngram_analyzer, search_analyzer=newline_analyzer)
    content_text = fields.TextField(attr='content_text', analyzer=ngram_analyzer, search_analyzer=newline_analyzer)
    created_by_nickname = fields.TextField(attr='created_by_nickname', analyzer=ngram_analyzer, search_analyzer=newline_analyzer)

    class Index:
        name = settings.ELASTICSEARCH_INDEX_NAME
        settings = {
            'number_of_shards': 3,
            'number_of_replicas': 1,
            'max_ngram_diff': 9,
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
    def get_id_set(q_object : Query):
        return [
            x.meta.id
            for x
            in ArticleDocument.search().query(q_object).sort('-created_at')[0:500].source(False).execute()
        ]

    @staticmethod
    def get_main_search_id_set(value):
        qt = 'multi_match' # query type: match. Use search_analyzer
        es_search_str = ''.join([
            f"{x.replace('_',' ')}\n" for x in value.split()
        ])

        return ArticleDocument.get_id_set(
            Q(qt, query=es_search_str, fields=['title', 'content_text', 'created_by_nickname'])
        )

    @staticmethod
    def get_instances_from_related(related_instance):
        if isinstance(related_instance, apps.get_model(settings.AUTH_USER_MODEL)):
            return related_instance.article_set.all()
        elif isinstance(related_instance, UserProfile):
            return related_instance.user.article_set.all()

