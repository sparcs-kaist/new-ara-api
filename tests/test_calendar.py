import pytest
from dateutil import parser
from django.utils import timezone
from rest_framework import status

from apps.calendar.models import Event, Tag
from tests.conftest import RequestSetting, TestCase


@pytest.fixture(scope="class", autouse=True)
def set_event(request):
    now = timezone.now()
    request.cls.event = Event.objects.create(
        is_all_day=False,
        start_at=now,
        end_at=now + timezone.timedelta(hours=1),
        ko_title="한글 제목",
        en_title="English Title",
        ko_description="한글 설명",
        en_description="English Description",
        location="장소",
        url="http://example.com/test",
    )
    request.cls.event.tags.add(
        Tag.objects.get_or_create(ko_name="아라", en_name="Ara", color="#ED3A3A")[0],
        Tag.objects.get_or_create(ko_name="스팍스", en_name="SPARCS", color="#EBA12A")[0],
    )


@pytest.mark.usefixtures("set_user_client", "set_event")
class TestCalendar(TestCase, RequestSetting):
    def test_list_count(self) -> None:
        res = self.http_request(self.user, "get", "calendar/events")
        assert res.status_code == status.HTTP_200_OK
        assert res.data.get("num_items") == Event.objects.count()

    def test_get(self) -> None:
        res = self.http_request(self.user, "get", f"calendar/events/{self.event.id}")
        assert res.status_code == status.HTTP_200_OK

        for el in res.data:
            if el == "tags":
                continue
            elif el == "start_at" or el == "end_at":
                assert parser.parse(res.data.get(el)) == getattr(self.event, el)
            else:
                assert res.data.get(el) == getattr(self.event, el)
