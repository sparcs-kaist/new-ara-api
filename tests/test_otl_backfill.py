from datetime import datetime
from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.course.models import CourseEnrollment
from apps.otl import sync
from ara import redis
from tests.conftest import RequestSetting, TestCase


def timetable(year, semester):
    return {"lectures": [{
        "id": year * 10 + semester, "courseId": 1, "code": f"CS{year}{semester}", "name": f"과목 {year}-{semester}",
        "credit": 3, "department": {"name": "전산학부"}, "professors": [{"id": 1, "name": "교수"}],
    }]}


@pytest.mark.usefixtures("set_user_client")
class TestOtlBackfill(TestCase, RequestSetting):
    def setUp(self):
        redis.delete(sync.backfill_key(self.user.id))
        self.user.profile.uid = "uid-1"
        self.user.profile.save()

    def tearDown(self):
        redis.delete(sync.backfill_key(self.user.id))

    def terms(self):
        return sorted(set(CourseEnrollment.objects.filter(user=self.user).values_list("course__year", "course__semester")))

    def test_backfill_terms_are_before_current(self):
        with patch.object(sync.timezone, "now", return_value=timezone.make_aware(datetime(2026, 9, 27))):
            terms = sync.backfill_terms()
        assert terms[0] == (2026, 2) and terms[-1] == (2022, 1)
        assert (2026, 3) not in terms and len(terms) == 18

    def test_first_visit_fills_past_terms_once(self):
        with patch.object(sync.client, "get_my_timetable", side_effect=lambda uid, y, s: timetable(y, s)) as otl:
            res = self.http_request(self.user, "get", "courses/me")
            assert res.status_code == 200
            cy, cs = sync.current_term()
            assert len(self.terms()) == len(sync.backfill_terms()) + 1
            calls = otl.call_count

            # 다음 방문에는 다시 채우지 않는다
            self.http_request(self.user, "get", "courses/me")
            assert otl.call_count == calls
        assert redis.get(sync.backfill_key(self.user.id)) == b"done"

    def test_failure_keeps_current_term_and_retries_later(self):
        def otl(uid, year, semester):
            if (year, semester) == sync.current_term():
                return timetable(year, semester)
            raise sync.OtlApiError("down")

        with patch.object(sync.client, "get_my_timetable", side_effect=otl):
            res = self.http_request(self.user, "get", "courses/me")
        assert res.status_code == 200
        assert [c["year"] for c in res.data] == [sync.current_term()[0]]
        # 끝까지 못 채웠으니 done 이 아니다 (한 시간 뒤 다시 시도)
        assert redis.get(sync.backfill_key(self.user.id)) == b"pending"
