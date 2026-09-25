from django.core.management import BaseCommand
from django_celery_beat.models import PeriodicTask

from ara import celery_app


# beat(DatabaseScheduler)는 코드의 beat_schedule 을 DB 에 덮어쓰지만, 코드에서 지운 작업은 DB 에 켜진 채로 남는다
class Command(BaseCommand):
    help = "Disable periodic tasks that are no longer in beat_schedule"

    def handle(self, *args, **options):
        keep = set(celery_app.conf.beat_schedule) | {"celery.backend_cleanup"}
        stale = PeriodicTask.objects.filter(enabled=True).exclude(name__in=keep)
        names = list(stale.values_list("name", flat=True))
        stale.update(enabled=False)
        self.stdout.write(f"disabled {len(names)} stale periodic tasks: {names}")
