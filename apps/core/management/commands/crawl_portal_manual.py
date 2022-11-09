from datetime import timedelta

from dateutil.parser import parse as date_parse
from django.core.management import BaseCommand
from django.utils import timezone

from apps.core.management.scripts.portal_crawler import crawl_hour


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--start")
        parser.add_argument("--end")

    def parse_date(self, options, arg_name):
        tz = timezone.get_current_timezone()
        date = options.get(arg_name, None)
        if date is not None:
            return tz.localize(date_parse(date)).date()
        else:
            return None

    def handle(self, *args, **options):
        start = self.parse_date(options, "start") or timezone.datetime.today().date()
        end = self.parse_date(options, "end") or timezone.datetime.today().date()

        print("start:", start, "end:", end)
        dates = []
        while start != end:
            dates.append(start)
            start += timedelta(days=1)

        dates.append(end)

        for date in dates:
            crawl_hour(day=date)
