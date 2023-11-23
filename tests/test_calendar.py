import pytest
from django.utils import timezone

from apps.calendar.models import Calendar
from tests.conftest import RequestSetting, TestCase, Utils


@pytest.fixture(scope="class", autouse=True)
def set_calendar(request):
    request.cls.calendar = Calendar.objects.create(
        is_allday=False,
        start_at=timezone.now(),
        end_at=timezone.now() + timezone.timedelta(hours=1),
        ko_title="테스트 캘린더",
        en_title="Test Calendar",
        ko_description="한글 설명",
        en_description="English Description",
        location="테스트 위치",
        url="http://example.com/test",
    )


class TestCalendar(TestCase, RequestSetting):
    # 모델의 생성 및 필드 확인
    def test_calendar_creation(self):
        assert self.calendar.is_allday == False
        assert self.calendar.start_at < self.calendar.end_at
        assert self.calendar.ko_title == "테스트 캘린더"
        assert self.calendar.en_title == "Test Calendar"
        assert self.calendar.ko_description == "한글 설명"
        assert self.calendar.en_description == "English Description"
        assert self.calendar.location == "테스트 위치"
        assert self.calendar.url == "http://example.com/test"


class TestCalendarAPI(TestCase, RequestSetting, Utils):
    def test_create_calendar(self):
        tags_data = [
            {"name": "Tag1", "color": "#FF0000"},
            {"name": "Tag2", "color": "#00FF00"},
        ]

        data = {
            "is_allday": False,
            "start_at": timezone.now(),
            "end_at": timezone.now() + timezone.timedelta(hours=1),
            "ko_title": "테스트 캘린더",
            "en_title": "Test Calendar",
            "ko_description": "한글 설명",
            "en_description": "English Description",
            "location": "테스트 위치",
            "url": "http://example.com/test",
            "tags": tags_data,
        }
        response = self.http_request(self.admin, "post", "calendars/", data=data)
        assert response.status_code == 201
        assert Calendar.objects.filter(ko_title="테스트 캘린더").exists()

        calendar = Calendar.objects.get(ko_title="테스트 캘린더")
        assert calendar.tags.count() == len(tags_data)

        for tag_data in tags_data:
            assert calendar.tags.filter(name=tag_data["name"]).exists()

    def test_get_calendar_list(self):
        self.create_calendar("Calendar 1")
        self.create_calendar("Calendar 2")

        response = self.http_request(self.admin, "get", "calendars/")
        assert response.status_code == 200
        assert len(response.data) == 2
