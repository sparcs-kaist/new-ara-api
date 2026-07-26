from django.apps import apps
from django.conf import settings
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from elasticsearch_dsl import Q, analyzer, tokenizer
from elasticsearch_dsl.analysis import token_filter
from elasticsearch_dsl.query import Query

from apps.core.article_scope import exclude_scoped_articles
from apps.core.models import Article
from apps.user.models import UserProfile

ngram_analyzer = analyzer(
    "ngram_anl",
    type="custom",
    tokenizer=tokenizer("ngram_tkn", type="char_group", tokenize_on_chars=["\n"]),
    filter=[
        token_filter(
            "ngram_tkf",
            type="ngram",
            min_gram=1,
            max_gram=10,
        ),
        "lowercase",
    ],
)


newline_analyzer = analyzer(
    "nl_anl",
    type="custom",
    tokenizer=tokenizer("nl_tkn", type="char_group", tokenize_on_chars=["\n"]),
    filter=[
        token_filter(
            "nl_syn_tkf",
            type="synonym",
            expand=True,
            synonyms_path="analysis/synonym.txt",
        ),
        "lowercase",
    ],
)


@registry.register_document
class ArticleDocument(Document):

    title = fields.TextField(
        attr="title", analyzer=ngram_analyzer, search_analyzer=newline_analyzer
    )
    content_text = fields.TextField(
        attr="content_text", analyzer=ngram_analyzer, search_analyzer=newline_analyzer
    )
    created_by_nickname = fields.TextField(
        attr="created_by_nickname",
        analyzer=ngram_analyzer,
        search_analyzer=newline_analyzer,
    )

    class Index:
        name = settings.ELASTICSEARCH_INDEX_NAME
        settings = {
            "number_of_shards": 3,
            "number_of_replicas": 1,
            "max_ngram_diff": 9,
        }

    class Django:
        model = Article

        fields = [
            "created_at",
        ]

        related_models = [settings.AUTH_USER_MODEL, UserProfile]

    def get_queryset(self):
        # 과목/학과 게시판 글은 색인 자체에서 뺀다. ES 안에는 Ara 의 권한 체계가
        # 없으므로, 색인에 들어가는 순간 검색 경로·ES 직접 접근 모두에서 본문이
        # 노출될 수 있다. 색인에 없으면 검색 관련 경로가 한 번에 정리된다.
        # (과목/학과 게시판 내 검색이 필요해지면 별도 인덱스로 분리할 것)
        return exclude_scoped_articles(
            super(ArticleDocument, self)
            .get_queryset()
            .prefetch_related("created_by")
            .prefetch_related("created_by__profile")
        )

    @staticmethod
    def get_id_set(q_object: Query):
        return [
            x.meta.id
            for x in ArticleDocument.search()
            .query(q_object)
            .sort("-created_at")[0:500]
            .source(False)
            .execute()
        ]

    @staticmethod
    def get_main_search_id_set(value):
        qt = "multi_match"  # query type: match. Use search_analyzer
        es_search_str = "".join([f"{x.replace('_',' ')}\n" for x in value.split()])

        return ArticleDocument.get_id_set(
            Q(
                qt,
                query=es_search_str,
                fields=["title", "content_text", "created_by_nickname"],
            )
        )

    @staticmethod
    def get_instances_from_related(related_instance):
        # 유저/프로필이 바뀌면 그 유저의 글을 재색인하는 경로. 여기서도 scoped
        # 글을 빼지 않으면 get_queryset 에서 제외한 글이 이 경로로 되살아난다.
        if isinstance(related_instance, apps.get_model(settings.AUTH_USER_MODEL)):
            return exclude_scoped_articles(related_instance.article_set.all())
        elif isinstance(related_instance, UserProfile):
            return exclude_scoped_articles(related_instance.user.article_set.all())
