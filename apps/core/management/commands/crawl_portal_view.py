from django.core.management import BaseCommand

from apps.core.management.scripts.portal_crawler import crawl_view


class Command(BaseCommand):
    help = "포탈 공지글의 조회수를 크롤링합니다"

    def handle(self, *args, **options):
        crawl_view()
