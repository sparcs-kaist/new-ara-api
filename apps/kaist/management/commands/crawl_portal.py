from django.core.management.base import BaseCommand

from apps.kaist.portal.worker import Worker


class Command(BaseCommand):
    help = "Crawl and save posts from the latest saved post up to the specified batch size."

    def add_arguments(self, parser):
        parser.add_argument(
            "--batch-size",
            default=32,
            type=int,
            help="Number of posts to crawl",
        )
        parser.add_argument(
            "--visualize",
            action="store_true",
            help="Visualize crawling progress",
        )

    def handle(self, *args, **options):
        Worker.fetch_and_save_from_the_latest(
            batch_size=options["batch_size"],
            visualize=options["visualize"],
        )
