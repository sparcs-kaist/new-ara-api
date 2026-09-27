from datetime import datetime
from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.course.models import CourseEnrollment
from apps.otl import sync
from ara import redis
from tests.conftest import RequestSetting, TestCase


def timetable(year, semester, code=None):
    return {"lectures": [{
        "id": year * 10 + semester, "courseId": 1, "code": code or f"CS{year}{semester}", "name": f"과목 {year}-{semester}",
        "credit": 3, "department": {"name": "전산학부"}, "professors": [{"id": 1, "name": "교수"}],
    }]}


def kst(*args):
    return timezone.make_aware(datetime(*args))


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

    def test_backfill_terms_go_back_to_2009(self):
        with patch.object(sync.timezone, "now", return_value=kst(2026, 9, 27)):
            terms = sync.backfill_terms()
        assert terms[0] == (2026, 2) and terms[-1] == (2009, 1)

    def test_stops_after_empty_streak_and_survives_gap(self):
        # 2023-2 ~ 2025-2 휴학 (9학기 공백) 을 건너 2022 까지 이어진다
        enrolled = {(2026, 1), (2025, 3), (2023, 1), (2022, 3)}

        def otl(uid, year, semester):
            return timetable(year, semester) if (year, semester) in enrolled else {"lectures": []}

        with patch.object(sync.timezone, "now", return_value=kst(2026, 9, 27)), \
                patch.object(sync.client, "get_my_timetable", side_effect=otl) as call:
            sync.backfill_past_terms(self.user)
        assert set(self.terms()) == enrolled
        # 2022-3 뒤로 12학기 비면 멈춘다 (2009 까지 가지 않는다)
        oldest = min((c.args[1], c.args[2]) for c in call.call_args_list)
        assert oldest == (2019, 3)
        assert redis.get(sync.backfill_key(self.user.id)) == b"done"

    def test_new_user_without_records_stops_early(self):
        with patch.object(sync.timezone, "now", return_value=kst(2026, 9, 27)), \
                patch.object(sync.client, "get_my_timetable", return_value={"lectures": []}) as call:
            sync.backfill_past_terms(self.user)
        assert call.call_count == sync.BACKFILL_EMPTY_STREAK - 1

    def test_first_visit_fills_once(self):
        with patch.object(sync.client, "get_my_timetable", side_effect=lambda uid, y, s: timetable(y, s)) as otl:
            assert self.http_request(self.user, "get", "courses/me").status_code == 200
            calls = otl.call_count
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
        assert redis.get(sync.backfill_key(self.user.id)) == b"pending"

    def test_term_synced_only_mid_semester_is_synced_again(self):
        # 2025 봄학기 중에 두 과목으로 sync
        with patch.object(sync.timezone, "now", return_value=kst(2025, 4, 1)), \
                patch.object(sync.client, "get_my_timetable", return_value={"lectures": timetable(2025, 1, "A")["lectures"] + timetable(2025, 1, "B")["lectures"]}):
            sync.sync_user_courses(self.user, 2025, 1)
        assert CourseEnrollment.objects.filter(user=self.user).count() == 2

        # 과거가 된 뒤: 종강 뒤 sync 가 없으니 다시 불러서 드랍(B)을 반영하고, 그 뒤로는 캐시
        with patch.object(sync.timezone, "now", return_value=kst(2026, 9, 27)), \
                patch.object(sync.client, "get_my_timetable", return_value=timetable(2025, 1, "A")) as call:
            sync.sync_user_courses(self.user, 2025, 1)
            sync.sync_user_courses(self.user, 2025, 1)
        assert call.call_count == 1
        assert list(CourseEnrollment.objects.filter(user=self.user).values_list("course__course_code", flat=True)) == ["A"]

    def test_refresh_runs_backfill_again(self):
        with patch.object(sync.client, "get_my_timetable", return_value={"lectures": []}) as otl:
            self.http_request(self.user, "get", "courses/me")
            # 현재 학기가 비어 있으면 현재 학기만 매번 다시 부른다
            calls = otl.call_count
            self.http_request(self.user, "get", "courses/me")
            assert otl.call_count == calls + 1
            calls = otl.call_count
            self.http_request(self.user, "get", "courses/me", querystring="refresh=true")
            assert otl.call_count > calls + 1


def test_backfill_runs_on_its_own_queue():
    from ara import celery_app

    route = celery_app.amqp.router.route({}, "apps.core.management.tasks.backfill_user_courses")
    assert route["queue"].name == "course"
