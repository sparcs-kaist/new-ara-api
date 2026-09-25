from django.core.management import call_command
from django_celery_beat.models import IntervalSchedule, PeriodicTask

from tests.conftest import TestCase


class TestDisableStalePeriodicTasks(TestCase):
    def test_disables_only_tasks_missing_from_code(self):
        every = IntervalSchedule.objects.create(every=10, period=IntervalSchedule.MINUTES)
        stale = PeriodicTask.objects.create(
            name="sync_portal_view_counts", task="apps.core.management.tasks.sync_portal_view_counts", interval=every,
        )
        kept = PeriodicTask.objects.create(
            name="crawl_meal", task="apps.core.management.tasks.crawl_meal", interval=every,
        )

        call_command("disable_stale_periodic_tasks")

        stale.refresh_from_db()
        kept.refresh_from_db()
        assert stale.enabled is False
        assert kept.enabled is True
