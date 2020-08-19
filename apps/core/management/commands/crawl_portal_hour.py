from django.core.management import BaseCommand

from apps.core.management.scripts.portal_crawler import crawl_hour


class Command(BaseCommand):
    def handle(self, *args, **options):
        crawl_hour()
