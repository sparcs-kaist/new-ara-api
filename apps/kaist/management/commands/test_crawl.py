from django.core.management.base import BaseCommand
from tqdm import tqdm

from apps.kaist.models import Post
from apps.kaist.portal.crawl_iterator import CrawlIterator
from ara.log import log


class Command(BaseCommand):
    help = "Crawl and save posts from the latest saved post up to the specified batch size."

    def add_arguments(self, parser):
        parser.add_argument(
            "--batch-size",
            default=32,
            type=int,
            help="Number of posts to crawl",
        )

    def handle(self, *args, **options):
        self.fetch_and_save_from_the_latest(batch_size=options["batch_size"])

    @staticmethod
    def fetch_and_save_from_the_latest(batch_size: int = 32):
        """
        Crawl and save posts from the latest saved post up to the specified batch size.
        Duplicate posts will be updated.

        :param batch_size: The number of posts to crawl at once
        """

        latest_post = Post.objects.latest("registered_at")
        posts = list(
            tqdm(
                iterable=CrawlIterator(
                    start_id=latest_post.id,
                    limit=batch_size,
                ),
                total=batch_size,
            )
        )

        Post.objects.bulk_create(
            objs=posts,
            update_conflicts=True,
            update_fields=(
                "title",
                "content",
                "next_post_id",
                "view_count",
                "changed_at",
                "changed_user_id",
                "updated_at",
            ),
        )

        log.info("All Done!")
