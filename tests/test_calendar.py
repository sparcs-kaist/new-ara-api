import pytest
from django.utils import timezone

from apps.calendar.models import Calendar
from tests.conftest import RequestSetting, TestCase


class TestCalendar(TestCase, RequestSetting):
    @pytest.fixture(scope="class")
    def set_calendar(self, request):
        request.cls.calendar = Calendar.objects.create(
            is_allday=True,
            start_at=timezone.now(),
            end_at=timezone.now() + timezone.timedelta(hours=1),
            ko_title="테스트 캘린더",
            en_title="Test Calendar",
            ko_description="한글 설명",
            en_description="English Description",
            location="테스트 위치",
            url="http://example.com/test",
        )

    def test_calendar_creation(self):
        assert self.calendar.is_allday
        assert self.calendar.start_at < self.calendar.end_at
        assert self.calendar.ko_title == "테스트 캘린더"
        assert self.calendar.en_title == "Test Calendar"
        assert self.calendar.ko_description == "한글 설명"
        assert self.calendar.en_description == "English Description"
        assert self.calendar.location == "테스트 위치"
        assert self.calendar.url == "http://example.com/test"
