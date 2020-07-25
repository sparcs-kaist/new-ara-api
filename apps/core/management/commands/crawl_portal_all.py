from django.core.management import BaseCommand

from apps.core.management.scripts.portal_crawler import crawl_all


class Command(BaseCommand):
    def handle(self, *args, **options):
        crawl_all()
