import hashlib
from collections import OrderedDict

import pytest
from django.core.management import call_command
from django.utils import timezone

from apps.core.models import Article, Board, Topic
from apps.core.models.board import NameType
from tests.conftest import RequestSetting, TestCase


@pytest.fixture(scope="class")
def set_board(request):
    request.cls.board = Board.objects.create(
        slug="test board",
        ko_name="테스트 게시판",
        en_name="Test Board",
    )


@pytest.fixture(scope="class")
def set_topic(request):
    """set_board 먼저 적용"""
    request.cls.topic = Topic.objects.create(
        slug="test topic",
        ko_name="테스트 토픽",
        en_name="Test Topic",
        ko_description="테스트용 토픽입니다",
        en_description="This is topic for testing",
        parent_board=request.cls.board,
    )


@pytest.fixture(scope="class")
def set_articles(request):
    """set_topic, set_user_client 먼저 적용. article 10개 생성"""

    def create_article(n):
        return Article.objects.create(
            title=f"Test Article{n}",
            content=f"Content of test article {n}",
            content_text=f"Content_text of test article {n}",
            name_type=NameType.REGULAR,
            is_content_sexual=False,
            is_content_social=False,
            hit_count=0,
            positive_vote_count=0,
            negative_vote_count=0,
            created_by=request.cls.user,
            parent_topic=request.cls.topic,
            parent_board=request.cls.board,
            commented_at=timezone.now(),
        )

    request.cls.articles = [create_article(i) for i in range(10)]


@pytest.fixture(scope="class")
def set_index(request):
    call_command("search_index", "--delete", "-f")
    call_command("search_index", "--create")


def generate_order(string):
    length = 10  # number of articles
    seed = int(
        hashlib.sha224(string.encode("utf-8")).hexdigest(), base=16
    )  # predictable 224-bit random integer seed

    # create an order of reading from the provided seed
    order = []
    while seed:
        order.append(seed % length)
        seed //= length

    # add unread articles
    for i in range(length):
        if i not in order:
            order.append(i)

    # the expected order is 'last read comes first', used OrderedDict to make distinct
    expected_order = list(OrderedDict.fromkeys(reversed(order)).keys())

    return order, expected_order


@pytest.mark.usefixtures(
    "set_user_client",
    "set_user_client2",
    "set_board",
    "set_topic",
    "set_index",
    "set_articles",
)
class TestRecent(TestCase, RequestSetting):
    def test_created_list(self):
        res = self.http_request(self.user, "get", "articles")
        assert res.data.get("num_items") == 10

    # 아무것도 읽지 않았을 때 recently_read는 empty array 임을 확인
    def test_recent_at_start(self):
        res = self.http_request(self.user, "get", "articles/recent")
        assert res.data.get("results") == []

    # article을 생 순서대로 읽었을 떄의 recent_articles 값 확인
    # GET 'recent'의 리턴 타입은 길이 5의 List[OrderedDict]임
    # OrderedDict의 array 임 (id, topic, create time 등 article의 모든 Field가 들어 있음)
    # array[0]이 가장 최근에 읽은 article 임
    def test_recent_order_written(self):
        for article in self.articles:
            self.http_request(self.user, "get", f"articles/{article.id}")

        recent_list = self.http_request(self.user, "get", "articles/recent").data.get(
            "results"
        )
        assert len(recent_list) == 10
        for i in range(10):
            assert recent_list[i]["id"] == self.articles[9 - i].id

    # article을 id 역순으로 읽었을 때의 recent_articles 값 확인
    def test_reverse_order_written(self):
        for article in reversed(self.articles):
            self.http_request(self.user, "get", f"articles/{article.id}")

        recent_list = self.http_request(self.user, "get", "articles/recent").data.get(
            "results"
        )
        assert len(recent_list) == 10
        for i in range(10):
            assert recent_list[i]["id"] == self.articles[i].id

    # 같은 article을 연속으로 여러번 읽었을 때 recent_articles
    def test_read_same_article_multiple_times_in_a_row(self):
        for article in self.articles[:8]:
            self.http_request(self.user, "get", f"articles/{article.id}")

        # Article 9를 3번 읽음
        for _ in range(3):
            self.http_request(self.user, "get", f"articles/{self.articles[8].id}")

        # Article 10을 3번 읽음
        for _ in range(3):
            self.http_request(self.user, "get", f"articles/{self.articles[9].id}")

        recent_list = self.http_request(self.user, "get", "articles/recent").data.get(
            "results"
        )
        assert len(recent_list) == 10
        # Article 9, 10이 한 번씩만 들어가 있는지 확인
        for i in range(10):
            assert recent_list[i]["id"] == self.articles[9 - i].id
        recent_list = self.http_request(self.user, "get", "articles/recent").data.get(
            "recently_read"
        )

    # 같은 article을 비연속적으로 여러번 읽었을 경우 확인 (전에 읽은 article 최근에 다시 읽었을 때)
    def test_read_same_article_multiple_times(self):
        # Article 1부터 10까지 순서대로 읽기
        for article in self.articles:
            self.http_request(self.user, "get", f"articles/{article.id}")

        # Article 3을 다시 읽기
        self.http_request(self.user, "get", f"articles/{self.articles[2].id}")
        recent_list = self.http_request(self.user, "get", "articles/recent").data.get(
            "results"
        )

        expected_order = [2, 9, 8, 7, 6, 5, 4, 3, 1, 0]
        for i in range(10):
            assert recent_list[i]["id"] == self.articles[expected_order[i]].id

    # 매우 복잡한 읽기 패턴에 대한 테스트
    def test_read_article_complex_pattern(self):
        order, expected_order = generate_order("foobarbaz")

        # read articles in created order
        for num in order:
            self.http_request(self.user, "get", f"articles/{self.articles[num].id}")

        recent_list = self.http_request(self.user, "get", "articles/recent").data.get(
            "results"
        )

        assert [x["id"] for x in recent_list] == [
            self.articles[x].id for x in expected_order
        ]

    # 매우 복잡한 읽기 패턴에 대한 side_article 테스트
    def test_read_article_complex_pattern_side_article(self):
        order, expected_order = generate_order("foobarbaz")

        for num in order:
            self.http_request(self.user, "get", f"articles/{self.articles[num].id}")

        i = len(expected_order) // 2

        before_id = self.articles[expected_order[i + 1]].id
        wanted_id = self.articles[expected_order[i]].id
        after_id = self.articles[expected_order[i - 1]].id

        resp = self.http_request(
            self.user, "get", f"articles/{wanted_id}", querystring="from_view=recent"
        ).data

        assert resp["side_articles"]["before"]["id"] == before_id
        assert resp["side_articles"]["after"]["id"] == after_id

    # 매우 복잡한 읽기 패턴에 대한 검색 테스트
    def test_read_article_complex_pattern_search(self):
        order, expected_order = generate_order("foobarbaz")

        for num in order:
            self.http_request(self.user, "get", f"articles/{self.articles[num].id}")

        # expected_order에서 3개를 선택하기 위해 서로 겹치지 않는 3개의 숫자 생성
        rand_selection = generate_order("foo")[1][:3]

        # expected_order의 순서를 보존하면서, rand_selection에 해당하는 원소만 뽑기
        expected_selection_order = [expected_order[x] for x in sorted(rand_selection)]
        # rand_selection에 해당하는 글들의 제목
        article_titles = " ".join(
            [f"Article{expected_order[x]}" for x in rand_selection]
        )

        recent_list = self.http_request(
            self.user,
            "get",
            "articles/recent",
            querystring=f"main_search__contains={article_titles}",
        ).data.get("results")

        # recent 검색결과가 expected_order의 순서를 그대로 유지하고 있는지 확인
        assert [x["id"] for x in recent_list] == [
            self.articles[x].id for x in expected_selection_order
        ]

    # 매우 복잡한 읽기 패턴에 대한 검색 및 side_article 테스트
    def test_read_article_complex_pattern_search_side_article(self):
        order, expected_order = generate_order("foobarbaz")

        for num in order:
            self.http_request(self.user, "get", f"articles/{self.articles[num].id}")

        rand_selection = generate_order("foo")[1][:3]

        expected_selection_order = [expected_order[x] for x in sorted(rand_selection)]
        article_titles = " ".join(
            [f"Article{expected_order[x]}" for x in rand_selection]
        )

        # recent 검색결과 3개 중 가장 덜 최근에 읽은 글의 id
        before_id = self.articles[expected_selection_order[2]].id
        # recent 검색결과 3개 중 중간 글의 id
        wanted_id = self.articles[expected_selection_order[1]].id
        # recent 검색결과 3개 중 가장 최근에 읽은 글의 id
        after_id = self.articles[expected_selection_order[0]].id

        resp = self.http_request(
            self.user,
            "get",
            f"articles/{wanted_id}",
            querystring=f"from_view=recent&search_query={article_titles}",
        ).data

        assert resp["side_articles"]["before"]["id"] == before_id
        assert resp["side_articles"]["after"]["id"] == after_id

    # 첫 번째 읽기가 from_view=recent일 경우 테스트
    def test_read_first_article_from_recent(self):
        resp = self.http_request(
            self.user,
            "get",
            f"articles/{self.articles[2].id}",
            querystring="from_view=recent",
        ).data
        assert resp["side_articles"]["before"] is None
        assert resp["side_articles"]["after"] is None
